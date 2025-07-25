"""Utils package for scraper_core"""

from .user_agents import (
    ALL_USER_AGENTS,
    DESKTOP_AGENTS,
    MOBILE_AGENTS,
    get_desktop_agent,
    get_mobile_agent,
    get_random_agent,
)

__all__ = [
    "DESKTOP_AGENTS",
    "MOBILE_AGENTS",
    "ALL_USER_AGENTS",
    "get_desktop_agent",
    "get_mobile_agent",
    "get_random_agent",
]
