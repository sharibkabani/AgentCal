"""
Streaming utility functions for the agent system.
"""

import logging
from typing import Any, Optional


def extract_usage_info(result) -> Optional[dict[str, Any]]:
    """Extract usage information from result."""
    try:
        if hasattr(result, "context_wrapper") and result.context_wrapper.usage:
            usage = result.context_wrapper.usage
            return {
                "requests": usage.requests,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error extracting usage info: {e}")
    return None
