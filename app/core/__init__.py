"""Core modules for the Bedrock-powered Graph + Memory POC."""

from .config import settings
from .bedrock import bedrock_client

__all__ = ["settings", "bedrock_client"]
