"""Tests for the AI agent layer — conversations, messages, feedback."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from tests.conftest import make_token


MOCK_LLM_RESPONSE = {
    "content": "Dit is een AI-gegenereerd concept-antwoord.",
    "model": "mistralai/mistral-small-latest",
    "prompt_tokens": 150,
    "completion_tokens": 42,
    "finish_reason": "stop",
}


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_agent_step(client, token, number="A.1"):
    """Create a step with a unique test number (A.x prefix) to avoid seed data collisions."""
    resp = await client.post(
        "/api/v1/steps/",
        json={
            "number": number,
            "phase": 0,
            "name": f"Agent Test Step {number}",
            "waarom_nu": "Test",
            "required_gremium": "sims",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_execution(client, token, step_id, status="in_uitvoering"):
    resp = await client.post(
        "/api/v1/steps/executions/",
        json={"step_id": step_id, "status": "niet_gestart"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    execution = resp.json()

    if status != "niet_gestart":
        resp = await client.patch(
            f"/api/v1/steps/executions/{execution['id']}",
            json={"status": status},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        execution = resp.json()

    return execution


# ── Tests: Start conversation ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_conversation(client: AsyncClient, test_tenant, tenant_token):
    """Starting a conversation creates it with a greeting message."""
    # Use step number "1" to match commitment-agent
    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_name"] == "commitment-agent"
    assert data["status"] == "active"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "assistant"
    assert "besluitmemo" in data["messages"][0]["content"].lower()


@pytest.mark.asyncio
async def test_start_conversation_resume_existing(client: AsyncClient, test_tenant, tenant_token):
    """Starting a conversation for the same execution returns the existing one."""
    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    resp1 = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp1.status_code == 201
    conv_id_1 = resp1.json()["id"]

    resp2 = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp2.status_code == 201
    conv_id_2 = resp2.json()["id"]
    assert conv_id_1 == conv_id_2


@pytest.mark.asyncio
async def test_start_conversation_wrong_agent(client: AsyncClient, test_tenant, tenant_token):
    """Cannot start a conversation with an agent that doesn't match the step."""
    # Create step with number "2a" but try commitment-agent (which expects "1")
    step = await _create_agent_step(client, tenant_token, number="2a")
    execution = await _create_execution(client, tenant_token, step["id"])

    resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 422
    assert "stap" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_conversation_unknown_agent(client: AsyncClient, test_tenant, tenant_token):
    """Unknown agent name returns 404."""
    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    resp = await client.post(
        "/api/v1/agents/nonexistent-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 404


# ── Tests: Get conversation ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_conversation(client: AsyncClient, test_tenant, tenant_token):
    """Can retrieve a conversation with its messages."""
    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    create_resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    conv_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/agents/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == conv_id
    assert len(data["messages"]) >= 1


@pytest.mark.asyncio
async def test_get_conversation_not_found(client: AsyncClient, tenant_token):
    """Returns 404 for nonexistent conversation."""
    resp = await client.get(
        f"/api/v1/agents/conversations/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 404


# ── Tests: Send message ─────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.services.agents.base_agent.llm_client.chat_completion", new_callable=AsyncMock)
async def test_send_message(mock_llm, client: AsyncClient, test_tenant, tenant_token):
    """Sending a message returns an assistant response and creates an audit log."""
    mock_llm.return_value = MOCK_LLM_RESPONSE

    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    create_resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    conv_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/agents/conversations/{conv_id}/messages",
        json={"content": "We willen beginnen met een IMS voor de hele gemeente."},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    assert data["content"] == MOCK_LLM_RESPONSE["content"]
    assert data["audit_log_id"] is not None

    mock_llm.assert_called_once()
    call_messages = mock_llm.call_args[0][0]
    assert call_messages[0]["role"] == "system"
    assert call_messages[-1]["role"] == "user"
    assert "IMS" in call_messages[-1]["content"]


@pytest.mark.asyncio
async def test_send_message_conversation_not_found(client: AsyncClient, tenant_token):
    """Sending to nonexistent conversation returns 404."""
    resp = await client.post(
        f"/api/v1/agents/conversations/{uuid.uuid4()}/messages",
        json={"content": "test"},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 404


# ── Tests: Feedback ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.services.agents.base_agent.llm_client.chat_completion", new_callable=AsyncMock)
async def test_submit_feedback(mock_llm, client: AsyncClient, test_tenant, tenant_token):
    """Submitting feedback updates the audit log."""
    mock_llm.return_value = MOCK_LLM_RESPONSE

    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    create_resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    conv_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/agents/conversations/{conv_id}/messages",
        json={"content": "test"},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )

    resp = await client.post(
        f"/api/v1/agents/conversations/{conv_id}/feedback",
        json={"feedback": "positief", "comment": "Goed concept"},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_submit_feedback_no_messages(client: AsyncClient, test_tenant, tenant_token):
    """Feedback on a conversation with no AI messages (only greeting without audit log) returns 404."""
    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    create_resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    conv_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/agents/conversations/{conv_id}/feedback",
        json={"feedback": "positief"},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 404


# ── Tests: RBAC ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_viewer_cannot_start_conversation(client: AsyncClient, test_tenant, tenant_token, viewer_token):
    """Viewer role cannot start conversations (requires tims_lid)."""
    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_can_read_conversation(client: AsyncClient, test_tenant, tenant_token, viewer_token):
    """Viewer role CAN read conversations."""
    step = await _create_agent_step(client, tenant_token, number="1")
    execution = await _create_execution(client, tenant_token, step["id"])

    create_resp = await client.post(
        "/api/v1/agents/commitment-agent/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    conv_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/agents/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 200


# ── Tests: All 7 agents loadable ────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("step_number,agent_name", [
    ("1", "commitment-agent"),
    ("2a", "context-agent"),
    ("2b", "scope-agent"),
    ("3a", "governance-agent"),
    ("4", "gap-agent"),
    ("5", "register-agent"),
    ("6", "controls-agent"),
])
async def test_all_agents_start(
    client: AsyncClient, test_tenant, tenant_token, step_number, agent_name
):
    """Each agent can start a conversation for its matching step."""
    step = await _create_agent_step(client, tenant_token, number=step_number)
    execution = await _create_execution(client, tenant_token, step["id"])

    resp = await client.post(
        f"/api/v1/agents/{agent_name}/conversations",
        json={"step_execution_id": execution["id"]},
        headers={"Authorization": f"Bearer {tenant_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_name"] == agent_name
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "assistant"
