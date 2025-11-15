"""
Memory storage and retrieval for the agent system.
"""

memory = []


def store_memory(source: str, content: str):
    """Store a memory entry with source and content."""
    memory.append({"source": source, "content": content})


def retrieve_memory(query: str, top_k: int = 3):
    """Retrieve the most recent memory entries.

    Args:
        query: Query string (currently unused, returns recent entries)
        top_k: Number of recent entries to return

    Returns:
        List of recent memory entries
    """
    return memory[-top_k:]
