"""
Webhook Endpoints

Receives webhooks from external systems (TopDesk, ServiceNow, etc.)
for real-time data updates.
"""

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Any, Dict, Optional
from datetime import datetime
import hmac
import hashlib
import logging

from sqlmodel import Session
from app.core.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256"
) -> bool:
    """Verify webhook signature using HMAC."""
    expected = hmac.new(
        secret.encode(),
        payload,
        getattr(hashlib, algorithm)
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


# =============================================================================
# TopDesk Webhooks
# =============================================================================

@router.post("/topdesk/asset")
async def topdesk_asset_webhook(
    request: Request,
    x_topdesk_signature: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Receive asset change notifications from TopDesk.

    TopDesk sends webhooks when assets are created, updated, or deleted.
    """
    payload = await request.body()

    # TODO: Verify signature with configured secret
    # if x_topdesk_signature:
    #     if not verify_webhook_signature(payload, x_topdesk_signature, TOPDESK_SECRET):
    #         raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = await request.json()
        event_type = data.get("eventType", "unknown")
        asset_data = data.get("asset", {})

        logger.info(f"TopDesk webhook: {event_type} for asset {asset_data.get('id')}")

        # TODO: Process the asset update
        # - Map TopDesk asset to IMS format
        # - Upsert to database

        return {
            "status": "received",
            "event_type": event_type,
            "asset_id": asset_data.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"TopDesk webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topdesk/incident")
async def topdesk_incident_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Receive incident notifications from TopDesk."""
    try:
        data = await request.json()
        event_type = data.get("eventType", "unknown")
        incident_data = data.get("incident", {})

        logger.info(f"TopDesk webhook: {event_type} for incident {incident_data.get('number')}")

        # TODO: Process incident update

        return {
            "status": "received",
            "event_type": event_type,
            "incident_number": incident_data.get("number"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"TopDesk incident webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ServiceNow Webhooks
# =============================================================================

@router.post("/servicenow/cmdb")
async def servicenow_cmdb_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Receive CMDB change notifications from ServiceNow.

    ServiceNow Business Rules can send outbound REST messages on CI changes.
    """
    try:
        data = await request.json()
        action = data.get("action", "unknown")  # insert, update, delete
        ci_data = data.get("ci", {})

        logger.info(f"ServiceNow webhook: {action} for CI {ci_data.get('sys_id')}")

        # TODO: Process CI update

        return {
            "status": "received",
            "action": action,
            "ci_sys_id": ci_data.get("sys_id"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"ServiceNow CMDB webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servicenow/incident")
async def servicenow_incident_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Receive incident notifications from ServiceNow."""
    try:
        data = await request.json()
        action = data.get("action", "unknown")
        incident_data = data.get("incident", {})

        logger.info(f"ServiceNow webhook: {action} for incident {incident_data.get('number')}")

        return {
            "status": "received",
            "action": action,
            "incident_number": incident_data.get("number"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"ServiceNow incident webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Proquro Webhooks
# =============================================================================

@router.post("/proquro/supplier")
async def proquro_supplier_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Receive supplier change notifications from Proquro."""
    try:
        data = await request.json()
        event = data.get("event", "unknown")
        supplier_data = data.get("supplier", {})

        logger.info(f"Proquro webhook: {event} for supplier {supplier_data.get('id')}")

        return {
            "status": "received",
            "event": event,
            "supplier_id": supplier_data.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Proquro webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proquro/contract")
async def proquro_contract_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Receive contract change notifications from Proquro."""
    try:
        data = await request.json()
        event = data.get("event", "unknown")
        contract_data = data.get("contract", {})

        logger.info(f"Proquro webhook: {event} for contract {contract_data.get('id')}")

        return {
            "status": "received",
            "event": event,
            "contract_id": contract_data.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Proquro contract webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# BlueDolphin Webhooks
# =============================================================================

@router.post("/bluedolphin/object")
async def bluedolphin_object_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Receive object change notifications from BlueDolphin."""
    try:
        data = await request.json()
        event = data.get("event", "unknown")
        object_data = data.get("object", {})

        logger.info(f"BlueDolphin webhook: {event} for object {object_data.get('id')}")

        return {
            "status": "received",
            "event": event,
            "object_id": object_data.get("id"),
            "object_type": object_data.get("type"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"BlueDolphin webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Generic Webhook (for custom integrations)
# =============================================================================

@router.post("/generic/{source}")
async def generic_webhook(
    source: str,
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Generic webhook endpoint for custom integrations.

    Use this for integrations that don't have a dedicated endpoint.
    """
    try:
        data = await request.json()

        logger.info(f"Generic webhook from {source}: {data.get('event', 'unknown')}")

        return {
            "status": "received",
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Generic webhook error from {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
