"""
Base Integration Client

Abstract base class for all external integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Awaitable
from pydantic import BaseModel
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)


class IntegrationConfig(BaseModel):
    """Configuration for an external integration."""
    name: str
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    enabled: bool = True
    sync_interval_minutes: int = 60
    last_sync: Optional[datetime] = None


class SyncResult(BaseModel):
    """Result of a sync operation."""
    integration: str
    entity_type: str
    success: bool
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: List[str] = []
    timestamp: datetime = datetime.utcnow()


# Type alias for upsert callbacks
# Callback signature: (external_id, external_source, mapped_data) -> (record, was_created)
UpsertCallback = Callable[[str, str, Dict[str, Any]], Awaitable[tuple]]


class BaseIntegration(ABC):
    """
    Abstract base class for external integrations.

    All integration clients should inherit from this class
    and implement the abstract methods.
    """

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=30.0,
        )
        self._setup_auth()

    def _setup_auth(self):
        """Configure authentication headers."""
        if self.config.api_key:
            self.client.headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self.config.username and self.config.password:
            import base64
            credentials = base64.b64encode(
                f"{self.config.username}:{self.config.password}".encode()
            ).decode()
            self.client.headers["Authorization"] = f"Basic {credentials}"

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the connection to the external system works."""
        pass

    @abstractmethod
    async def sync_assets(self) -> SyncResult:
        """Sync assets from the external system."""
        pass

    @abstractmethod
    async def sync_suppliers(self) -> SyncResult:
        """Sync suppliers/vendors from the external system."""
        pass

    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request to the external API."""
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in {self.config.name}: {e}")
            raise

    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the external API."""
        try:
            response = await self.client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in {self.config.name}: {e}")
            raise
