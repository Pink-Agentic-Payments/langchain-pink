"""Integration tests against the LIVE Pink sandbox (test money only).

Creates one fresh sandbox workspace (template="startup") and drives the
LangChain tools through all three payment decisions, using the known
payee "Figma" (p_figma) and amounts that were live-probed against this
same template on 2026-10-12 (see NOTES.md):

    $50    -> allowed       (rule r12: known vendors under $1,000)
    $2,000 -> pending_human (rule r13: $1,000-$5,000, CFO approves)
    $10,000 -> blocked      (agent's monthly budget is used up)

Run with:

    pytest tests/integration_tests -v -s
"""
import json

import pytest
from pink_agentic_payments import approve_payment, create_sandbox_workspace

from langchain_pink.tools import (
    PinkCheckPaymentStatusTool,
    PinkCheckPolicyTool,
    PinkGetBudgetTool,
    PinkRequestPaymentTool,
)


def _log(label, value):
    print(f"\n--- {label} ---\n{json.dumps(value, indent=2) if isinstance(value, dict) else value}")


@pytest.fixture(scope="module")
def workspace():
    ws = create_sandbox_workspace(company="LangChain Pink Integration Test", template="startup")
    _log("created workspace_id (test money only; see NOTES.md)", ws["workspace_id"])
    return ws


@pytest.fixture(scope="module")
def agent_key(workspace):
    return workspace["agents"][0]["key"]


@pytest.fixture(scope="module")
def admin_key(workspace):
    return workspace["admin_key"]


def test_get_budget_live(agent_key):
    tool = PinkGetBudgetTool(agent_key=agent_key)
    out = tool.invoke({})
    _log("get_budget result", out)
    assert "left_this_month=" in out


def test_check_policy_live(agent_key):
    tool = PinkCheckPolicyTool(agent_key=agent_key)
    out = tool.invoke({"amount": 50, "payee_id": "p_figma", "purpose": "design tool renewal"})
    _log("check_policy result", out)
    assert "would_decision=would_allow" in out


def test_request_payment_allowed_live(agent_key):
    tool = PinkRequestPaymentTool(agent_key=agent_key)
    out = tool.invoke({"amount": 50, "currency": "USD", "payee_id": "p_figma", "purpose": "design tool renewal"})
    _log("request_payment (expect allowed)", out)
    assert "decision=allowed" in out


def test_request_payment_blocked_live(agent_key):
    tool = PinkRequestPaymentTool(agent_key=agent_key)
    out = tool.invoke({"amount": 10000, "currency": "USD", "payee_id": "p_figma", "purpose": "large annual license"})
    _log("request_payment (expect blocked)", out)
    assert "decision=blocked" in out


def test_request_payment_pending_human_live(agent_key, admin_key):
    pay_tool = PinkRequestPaymentTool(agent_key=agent_key)
    status_tool = PinkCheckPaymentStatusTool(agent_key=agent_key)

    out = pay_tool.invoke({"amount": 2000, "currency": "USD", "payee_id": "p_figma", "purpose": "team license upgrade"})
    _log("request_payment (expect pending_human)", out)
    assert "decision=pending_human" in out

    payment_id = out.split("payment_id=")[1].split(" ")[0]
    approve_payment(admin_key, payment_id, by="Integration test admin")
    status_out = status_tool.invoke({"payment_id": payment_id})
    _log("check_payment_status after admin approval", status_out)
    # A human-approved hold reports decision="approved" (distinct from the
    # immediate "allowed" a fresh request_payment() call returns), live-verified
    # 2026-10-12 against this same sandbox.
    assert "decision=approved" in status_out
    assert "credential_type=" in status_out
