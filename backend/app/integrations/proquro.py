"""
Proquro Integration Client

Syncs supplier/vendor data and contracts from Proquro.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from app.integrations.base import BaseIntegration, IntegrationConfig, SyncResult

logger = logging.getLogger(__name__)


class ProquroClient(BaseIntegration):
    """
    Proquro API client for syncing supplier management data.

    Supported entities:
    - Suppliers/Vendors
    - Contracts
    - Risk assessments
    - SLA data
    """

    async def test_connection(self) -> bool:
        """Test connection to Proquro API."""
        try:
            await self._get("/api/v1/health")
            return True
        except Exception as e:
            logger.error(f"Proquro connection test failed: {e}")
            return False

    async def sync_assets(self) -> SyncResult:
        """
        Proquro doesn't have assets - return empty result.
        """
        return SyncResult(
            integration="proquro",
            entity_type="assets",
            success=True,
            errors=["Proquro does not provide asset data"],
        )

    async def sync_suppliers(self) -> SyncResult:
        """
        Sync suppliers from Proquro.

        Includes contract and risk information.
        """
        result = SyncResult(
            integration="proquro",
            entity_type="suppliers",
            success=True,
        )

        try:
            # Fetch suppliers from Proquro
            response = await self._get("/api/v1/suppliers", params={
                "limit": 500,
                "include": "contracts,risks,contacts",
            })

            suppliers = response.get("data", [])

            for supplier in suppliers:
                try:
                    mapped_supplier = self._map_supplier(supplier)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Supplier {supplier.get('id')}: {str(e)}")

            logger.info(f"Proquro sync: {result.created} suppliers synced")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Proquro supplier sync failed: {e}")

        return result

    async def sync_contracts(self) -> SyncResult:
        """Sync contracts from Proquro."""
        result = SyncResult(
            integration="proquro",
            entity_type="contracts",
            success=True,
        )

        try:
            response = await self._get("/api/v1/contracts", params={
                "limit": 500,
                "status": "active",
            })

            contracts = response.get("data", [])

            for contract in contracts:
                try:
                    mapped_contract = self._map_contract(contract)
                    # TODO: Link to supplier and store
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Contract {contract.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def sync_supplier_risks(self) -> SyncResult:
        """Sync supplier risk assessments from Proquro."""
        result = SyncResult(
            integration="proquro",
            entity_type="supplier_risks",
            success=True,
        )

        try:
            response = await self._get("/api/v1/risk-assessments", params={
                "limit": 500,
            })

            assessments = response.get("data", [])

            for assessment in assessments:
                try:
                    # TODO: Map to IMS risk model
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Risk {assessment.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _map_supplier(self, proquro_supplier: Dict[str, Any]) -> Dict[str, Any]:
        """Map Proquro supplier to IMS Supplier format."""
        contacts = proquro_supplier.get("contacts", [])
        primary_contact = contacts[0] if contacts else {}

        return {
            "external_id": proquro_supplier.get("id"),
            "external_source": "proquro",
            "name": proquro_supplier.get("name", "Unknown"),
            "description": proquro_supplier.get("description", ""),
            "contact_name": primary_contact.get("name"),
            "contact_email": primary_contact.get("email"),
            "contact_phone": primary_contact.get("phone"),
            "website": proquro_supplier.get("website"),
            "risk_level": self._map_risk_level(proquro_supplier.get("risk_rating")),
            "status": self._map_status(proquro_supplier.get("status")),
            "metadata": {
                "proquro_id": proquro_supplier.get("id"),
                "category": proquro_supplier.get("category"),
                "contracts_count": len(proquro_supplier.get("contracts", [])),
                "last_assessment_date": proquro_supplier.get("last_assessment_date"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_contract(self, proquro_contract: Dict[str, Any]) -> Dict[str, Any]:
        """Map Proquro contract to IMS format."""
        return {
            "external_id": proquro_contract.get("id"),
            "external_source": "proquro",
            "supplier_external_id": proquro_contract.get("supplier_id"),
            "name": proquro_contract.get("title", "Unknown"),
            "start_date": proquro_contract.get("start_date"),
            "end_date": proquro_contract.get("end_date"),
            "value": proquro_contract.get("total_value"),
            "status": proquro_contract.get("status"),
            "metadata": {
                "proquro_id": proquro_contract.get("id"),
                "contract_type": proquro_contract.get("type"),
                "renewal_type": proquro_contract.get("renewal_type"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_risk_level(self, rating: Optional[str]) -> str:
        """Map Proquro risk rating to IMS risk level."""
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "minimal": "low",
        }
        return mapping.get(str(rating).lower(), "medium")

    def _map_status(self, status: Optional[str]) -> str:
        """Map Proquro status to IMS status."""
        mapping = {
            "active": "active",
            "inactive": "inactive",
            "pending": "pending_review",
            "blocked": "inactive",
            "archived": "inactive",
        }
        return mapping.get(str(status).lower(), "active")
