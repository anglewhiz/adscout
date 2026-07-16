"""AdScout — ask marketing questions, get answers proven with competitive-intelligence data."""
from .analyst import Analyst, AnalystResult
from .client import SpyFuClient, SpyFuError
from .config import Settings

__all__ = ["Analyst", "AnalystResult", "SpyFuClient", "SpyFuError", "Settings"]
__version__ = "0.1.0"
