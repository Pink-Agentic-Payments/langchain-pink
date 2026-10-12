"""Plain unit tests: no network, mock the PinkClient methods."""
from unittest.mock import MagicMock

import pytest
from pink_agentic_payments import PinkApprovalPending, PinkPolicyDenied

from langchain_pink.tools import (
    AGENT_KEY_ENV_VAR,
    PinkCheckPaymentStatusTool,
    PinkCheckPolicyTool,
    PinkGetBudgetTool,
    PinkRequestPaymentTool,
)


def _tool_with_mock_client(tool_cls, mock_client):
    tool = tool_cls(agent_key="pk_sandbox_agent_fake")
    tool.client = mock_client
    return tool


def test_request_payment_allowed():
    client = MagicMock()
    client.request_payment.return_value = {
        "payment_id": "pay_1",
        "decision": "allowed",
        "credential": {"type": "bank_transfer"},
    }
    tool = _tool_with_mock_client(PinkRequestPaymentTool, client)
    out = tool.invoke({"amount": 10, "merchant": "Blue Bottle Coffee", "purpose": "beans"})
    assert "decision=allowed" in out
    assert "credential_type=bank_transfer" in out
    client.request_payment.assert_called_once()


def test_request_payment_blocked():
    client = MagicMock()
    client.request_payment.side_effect = PinkPolicyDenied(
        {"payment_id": "pay_2", "decision": "blocked", "rule": "Never: gift cards"}
    )
    tool = _tool_with_mock_client(PinkRequestPaymentTool, client)
    out = tool.invoke({"amount": 999999, "merchant": "Gift Card Co"})
    assert "decision=blocked" in out
    assert "Never: gift cards" in out


def test_request_payment_pending_human():
    client = MagicMock()
    client.request_payment.side_effect = PinkApprovalPending(
        {"payment_id": "pay_3", "decision": "pending_human", "who": "Maya Chen (Owner)"}
    )
    tool = _tool_with_mock_client(PinkRequestPaymentTool, client)
    out = tool.invoke({"amount": 500, "merchant": "Office Supplies Co"})
    assert "decision=pending_human" in out
    assert "Maya Chen" in out


def test_check_policy():
    client = MagicMock()
    client.check_policy.return_value = {"decision": "would_allow", "reason": "Small supply orders go through"}
    tool = _tool_with_mock_client(PinkCheckPolicyTool, client)
    out = tool.invoke({"amount": 10, "merchant": "Blue Bottle Coffee"})
    assert "would_decision=would_allow" in out


def test_get_budget():
    client = MagicMock()
    client.get_budget.return_value = {
        "monthly_budget": 25000,
        "spent_this_month": 17840,
        "left_this_month": 7160,
        "single_payment_cap": 1000,
        "vault": {"balances": {"USD": 58900}},
    }
    tool = _tool_with_mock_client(PinkGetBudgetTool, client)
    out = tool.invoke({})
    assert "left_this_month=7160" in out


def test_check_payment_status():
    client = MagicMock()
    client.get_payment.return_value = {"decision": "allowed", "credential": {"type": "virtual_card"}}
    tool = _tool_with_mock_client(PinkCheckPaymentStatusTool, client)
    out = tool.invoke({"payment_id": "pay_4"})
    assert "decision=allowed" in out
    assert "credential_type=virtual_card" in out


def test_missing_agent_key_raises(monkeypatch):
    monkeypatch.delenv(AGENT_KEY_ENV_VAR, raising=False)
    tool = PinkGetBudgetTool()
    with pytest.raises(ValueError):
        tool.invoke({})


def test_agent_key_from_env(monkeypatch):
    monkeypatch.setenv(AGENT_KEY_ENV_VAR, "pk_sandbox_agent_from_env")
    tool = PinkGetBudgetTool()
    client = tool._get_client()
    assert client.agent_key == "pk_sandbox_agent_from_env"
