"""
Utility functions for mpspline package.

Helper functions for logging, data formatting, and common operations.
"""

import logging


# Configure module logger
def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a configured logger for the module.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))

    return logger


def format_depth_key(property_name: str, depth_top: int, depth_bottom: int) -> str:
    """
    Format a standard depth-property column name.

    Args:
        property_name: Name of property (e.g., 'clay')
        depth_top: Top of depth interval (cm)
        depth_bottom: Bottom of depth interval (cm)

    Returns:
        Formatted column name (e.g., 'clay_0_5')
    """
    return f"{property_name}_{depth_top}_{depth_bottom}"


def parse_depth_key(key: str) -> tuple | None:
    """
    Parse a depth-property column name back to components.

    Args:
        key: Column name (e.g., 'clay_0_5')

    Returns:
        Tuple of (property_name, depth_top, depth_bottom) or None if not parseable
    """
    try:
        parts = key.rsplit("_", 2)
        if len(parts) != 3:
            return None

        property_name = parts[0]
        depth_top = int(parts[1])
        depth_bottom = int(parts[2])

        return property_name, depth_top, depth_bottom
    except (ValueError, AttributeError):
        return None
