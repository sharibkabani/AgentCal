from agents import Runner
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse
import json

# Import from refactored modules
from memory import retrieve_memory
from agent_definitions.calendar_agents import triage_agent
from streaming.formatters import format_stream_event
from streaming.utils import extract_usage_info

logging.getLogger("openai.agents").setLevel(logging.DEBUG)
logging.getLogger("openai.agents").addHandler(logging.StreamHandler())

load_dotenv()
app = FastAPI()

# Configure CORS to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/agent")
async def agent(request: dict):
    """
    Main agent endpoint that uses a triage agent to route requests
    to specialist agents for calendar operations.
    """
    logger = logging.getLogger(__name__)
    user_input = request.get("user_input")
    logger.info(f"🤖 Agent received request: {user_input[:100]}...")

    # Get current date/time information with timezone
    import tzlocal

    local_tz = tzlocal.get_localzone()
    now = datetime.now(local_tz)
    tz_name = now.strftime("%Z")

    current_date_info = f"""Current Date/Time Information:
- Today's date: {now.strftime("%Y-%m-%d")} ({now.strftime("%A, %B %d, %Y")})
- Current time: {now.strftime("%H:%M:%S")}
- Timezone: {tz_name} (IANA: {str(local_tz)})
- Current datetime (ISO format with timezone): {now.isoformat()}
- Day of week: {now.strftime("%A")}
- Week of year: {now.strftime("%U")}

IMPORTANT: When creating calendar events or meetings, always specify times in the user's timezone ({tz_name}).
Use this information to interpret relative dates like "today", "tomorrow", "next week", etc.
"""

    mem = retrieve_memory(user_input)
    prompt = f"""{current_date_info}

Context from memory: {mem}

User input: {user_input}"""

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            logger.info(
                f"🚀 Running triage agent with current date: {now.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            # Use the triage agent which will hand off to specialist agents
            result = Runner.run_streamed(triage_agent, input=prompt)

            # Wrap event streaming with error handling for Union type issues
            try:
                async for event in result.stream_events():
                    try:
                        # Process each event type with proper serialization
                        formatted_event = format_stream_event(event, logger)
                        if formatted_event:
                            yield f"data: {json.dumps(formatted_event)}\n\n"
                    except AttributeError as attr_err:
                        # Handle Union type discriminator errors
                        if "__discriminator__" in str(attr_err):
                            logger.warning(
                                f"Skipping event due to Union type issue: {attr_err}"
                            )
                            continue
                        else:
                            raise
                    except Exception as e:
                        logger.error(f"Error processing individual event: {e}")
                        # Continue with next event instead of failing entirely
                        continue
            except AttributeError as attr_err:
                # Handle Union type discriminator errors during iteration
                if "__discriminator__" in str(attr_err):
                    logger.error(
                        f"Stream iteration failed due to Union type issue: {attr_err}"
                    )
                    # Try to get final output despite streaming failure
                    try:
                        completion_event = {
                            "type": "stream_complete",
                            "final_output": result.final_output
                            if hasattr(result, "final_output")
                            else "Error during streaming",
                            "error": "Streaming interrupted due to Union type issue",
                        }
                        yield f"data: {json.dumps(completion_event)}\n\n"
                        return
                    except Exception:
                        pass
                raise

            # Send completion event
            completion_event = {
                "type": "stream_complete",
                "final_output": result.final_output,
                "current_turn": result.current_turn,
                "usage": extract_usage_info(result)
                if hasattr(result, "usage")
                else None,
            }
            yield f"data: {json.dumps(completion_event)}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}", exc_info=True)
            error_event = {
                "type": "error",
                "message": str(e),
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@app.get("/")
def read_root():
    return {"Hello": "World"}
