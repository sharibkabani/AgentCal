"""
Stream event formatters for the agent system.
"""

import logging
from typing import Any, Optional
from agents.stream_events import StreamEvent


def format_stream_event(
    event: StreamEvent, logger: logging.Logger
) -> Optional[dict[str, Any]]:
    """
    Format stream events into a consistent, frontend-friendly structure.

    This avoids double JSON encoding and provides clean event structures.
    Uses event.type to check event types as per OpenAI Agents SDK documentation.
    """
    try:
        # Safely access event.type - handle Union type issues
        event_type = None
        try:
            # Try direct attribute access first
            if hasattr(event, "type"):
                event_type = event.type
        except (AttributeError, TypeError) as e:
            # If direct access fails, try getattr
            logger.debug(f"Direct access failed, using getattr: {e}")
            event_type = getattr(event, "type", None)

        # If we still don't have a type, try to infer from the event object itself
        if event_type is None:
            # Check the actual class name as fallback
            event_class_name = type(event).__name__
            logger.warning(f"Event has no type attribute, class: {event_class_name}")
            if "RawResponse" in event_class_name:
                event_type = "raw_response_event"
            elif "RunItem" in event_class_name:
                event_type = "run_item_stream_event"
            elif "AgentUpdated" in event_class_name:
                event_type = "agent_updated_stream_event"

        if event_type == "raw_response_event":
            formatted_event = format_raw_response_event(event, logger)
        elif event_type == "run_item_stream_event":
            formatted_event = format_run_item_event(event, logger)
        elif event_type == "agent_updated_stream_event":
            formatted_event = format_agent_updated_event(event, logger)
        else:
            # Fallback for unknown event types - try to serialize what we can
            logger.warning(
                f"Unknown event type: {event_type}, class: {type(event).__name__}"
            )
            formatted_event = {
                "type": "unknown_event",
                "event_type": event_type,
                "event_class": type(event).__name__,
            }

        return formatted_event
    except Exception as e:
        logger.error(f"Error formatting event: {e}", exc_info=True)
        # Return a minimal error event so frontend knows something happened
        return {
            "type": "error",
            "message": str(e),
            "event_class": type(event).__name__ if event else "None",
        }


def format_raw_response_event(
    event: StreamEvent, logger: logging.Logger
) -> dict[str, Any]:
    """Format raw response events with proper JSON structure."""
    try:
        # Safely access event.data - handle Union type issues
        event_data = None
        try:
            if hasattr(event, "data"):
                event_data = event.data
        except (AttributeError, TypeError):
            event_data = getattr(event, "data", None)

        if event_data is None:
            logger.warning("Raw response event has no data attribute")
            return {"type": "raw_response", "error": "No data in event"}

        # Safely get event_type from event_data
        event_type = None
        try:
            if hasattr(event_data, "type"):
                event_type = event_data.type
        except (AttributeError, TypeError):
            event_type = getattr(event_data, "type", "unknown")

        base_event = {
            "type": "raw_response",
            "event_type": event_type or "unknown",
            "sequence_number": getattr(event_data, "sequence_number", None),
        }

        # Handle specific raw event types
        if event_type:
            # Text streaming events
            if event_type == "response.output_text.delta":
                base_event.update(
                    {
                        "delta": getattr(event_data, "delta", ""),
                        "content_index": getattr(event_data, "content_index", 0),
                        "item_id": getattr(event_data, "item_id", None),
                        "output_index": getattr(event_data, "output_index", 0),
                    }
                )

            # Reasoning events (for models like deepseek-reasoner)
            elif event_type == "response.reasoning_summary_text.delta":
                base_event.update(
                    {"delta": getattr(event_data, "delta", ""), "reasoning": True}
                )

            # Refusal events
            elif event_type == "response.refusal.delta":
                base_event.update(
                    {"delta": getattr(event_data, "delta", ""), "refusal": True}
                )

            # Capture tool name when tool call starts
            elif event_type == "response.output_item.added":
                item_obj = getattr(event_data, "item", None)
                base_event.update(
                    {
                        "output_index": getattr(event_data, "output_index", 0),
                        "item_type": getattr(item_obj, "type", None)
                        if item_obj
                        else None,
                    }
                )

                # Extract tool name if this is a function tool call
                if item_obj and hasattr(item_obj, "name"):
                    base_event.update(
                        {
                            "tool_name": item_obj.name,
                            "call_id": getattr(item_obj, "call_id", None),
                        }
                    )

            # Function call arguments
            elif event_type == "response.function_call_arguments.delta":
                base_event.update(
                    {
                        "delta": getattr(event_data, "delta", ""),
                        "function_call": True,
                        "call_id": getattr(event_data, "call_id", None),
                    }
                )

            # Response lifecycle events
            elif event_type in ["response.created", "response.completed"]:
                response_obj = getattr(event_data, "response", None)
                base_event.update(
                    {
                        "response_id": getattr(response_obj, "id", None)
                        if response_obj
                        else None,
                        "status": getattr(response_obj, "status", None)
                        if response_obj
                        else None,
                    }
                )

            # Content lifecycle events
            elif event_type in [
                "response.content_part.added",
                "response.content_part.done",
            ]:
                base_event.update(
                    {
                        "content_index": getattr(event_data, "content_index", 0),
                        "item_id": getattr(event_data, "item_id", None),
                    }
                )

            # Output item events
            elif event_type in [
                "response.output_item.added",
                "response.output_item.done",
            ]:
                item_obj = getattr(event_data, "item", None)
                base_event.update(
                    {
                        "output_index": getattr(event_data, "output_index", 0),
                        "item_type": getattr(item_obj, "type", None)
                        if item_obj
                        else None,
                    }
                )

            # Text completion events
            elif event_type == "response.output_text.done":
                base_event.update(
                    {
                        "text": getattr(event_data, "text", ""),
                        "content_index": getattr(event_data, "content_index", 0),
                        "item_id": getattr(event_data, "item_id", None),
                    }
                )

        return base_event
    except Exception as e:
        logger.error(f"Error formatting raw response event: {e}", exc_info=True)
        return {"type": "raw_response", "error": str(e)}


def format_run_item_event(event: StreamEvent, logger: logging.Logger) -> dict[str, Any]:
    """Format run item events (semantic agent events)."""
    try:
        # Safely access event attributes - handle Union type issues
        event_name = None
        event_item = None

        try:
            if hasattr(event, "name"):
                event_name = event.name
            if hasattr(event, "item"):
                event_item = event.item
        except (AttributeError, TypeError):
            event_name = getattr(event, "name", None)
            event_item = getattr(event, "item", None)

        base_event = {
            "type": "run_item",
            "name": event_name,
            "item_type": getattr(event_item, "type", None) if event_item else None,
        }

        # Handle specific run item types
        if event_name == "message_output_created":
            base_event.update(
                {
                    "role": getattr(event_item, "role", None),
                    "status": getattr(event_item, "status", None),
                    "message_id": getattr(event_item, "id", None),
                }
            )

        elif event_name == "tool_called":
            raw_item = getattr(event_item, "raw_item", None) if event_item else None
            base_event.update(
                {
                    "tool_name": getattr(raw_item, "name", None) if raw_item else None,
                    "tool_arguments": getattr(raw_item, "arguments", None)
                    if raw_item
                    else None,
                    "call_id": getattr(raw_item, "id", None) if raw_item else None,
                }
            )

        elif event_name == "tool_output":
            base_event.update(
                {
                    "tool_name": getattr(event_item, "name", None),
                    "output": getattr(event_item, "output", None),
                    "call_id": getattr(event_item, "id", None),
                }
            )

        elif event_name == "handoff_requested":
            base_event.update(
                {
                    "target_agent": getattr(event_item, "target_agent_name", None),
                    "reason": getattr(event_item, "reason", None),
                }
            )

        elif event_name == "handoff_occured":
            base_event.update(
                {
                    "target_agent": getattr(event_item, "target_agent_name", None),
                    "previous_agent": getattr(event_item, "previous_agent_name", None),
                }
            )

        elif event_name == "reasoning_item_created":
            base_event.update(
                {"reasoning_content": getattr(event_item, "content", None)}
            )

        # MCP-related events
        elif event_name == "mcp_approval_requested":
            base_event.update(
                {
                    "tool_name": getattr(event_item, "tool_name", None),
                    "server_name": getattr(event_item, "server_name", None),
                }
            )

        elif event_name == "mcp_list_tools":
            base_event.update(
                {
                    "server_name": getattr(event_item, "server_name", None),
                    "tools": getattr(event_item, "tools", []),
                }
            )

        return base_event
    except Exception as e:
        logger.error(f"Error formatting run item event: {e}", exc_info=True)
        return {"type": "run_item", "error": str(e)}


def format_agent_updated_event(
    event: StreamEvent, logger: logging.Logger
) -> dict[str, Any]:
    """Format agent updated events (handoffs)."""
    try:
        # Safely access new_agent attribute - handle Union type issues
        new_agent = None
        try:
            if hasattr(event, "new_agent"):
                new_agent = event.new_agent
        except (AttributeError, TypeError):
            new_agent = getattr(event, "new_agent", None)

        if new_agent is None:
            logger.warning("Agent updated event has no new_agent attribute")
            return {"type": "agent_updated", "error": "No new_agent in event"}

        return {
            "type": "agent_updated",
            "agent_name": getattr(new_agent, "name", None),
            "agent_instructions": new_agent.instructions
            if isinstance(getattr(new_agent, "instructions", None), str)
            else "Dynamic instructions",
            "model": str(getattr(new_agent, "model", None))
            if getattr(new_agent, "model", None)
            else None,
            "tools_count": len(getattr(new_agent, "tools", [])),
            "handoffs_count": len(getattr(new_agent, "handoffs", [])),
        }
    except Exception as e:
        logger.error(f"Error formatting agent updated event: {e}", exc_info=True)
        return {"type": "agent_updated", "error": str(e)}
