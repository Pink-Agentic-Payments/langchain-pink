"""BaseTool wrappers around the pink-agentic-payments sandbox client.

Each tool maps 1:1 to one method of ``pink_agentic_payments.PinkClient``
(see that package's NOTES.md for the endpoint-by-method mapping). No new
capability is invented here: every tool just gives an LLM a typed,
documented way to call a method that already exists in the official client.

Sandbox only, test money: see https://pinkwallet.com/agentic/developers/.
"""
from __future__ import annotations

import os
from typing import Optional, Type

from langchain_core.tools import BaseTool
from pink_agentic_payments import (
    PinkApprovalPending,
    PinkClient,
    PinkPolicyDenied,
)
from pink_agentic_payments.exceptions import PinkAPIError
from pydantic import BaseModel, Field

AGENT_KEY_ENV_VAR = "PINK_AGENT_API_KEY"


def _resolve_client(agent_key: Optional[str], base_url: Optional[str]) -> PinkClient:
    key = agent_key or os.environ.get(AGENT_KEY_ENV_VAR)
    if not key:
        raise ValueError(
            f"No Pink agent key given and {AGENT_KEY_ENV_VAR} is not set. "
            "Get a free sandbox agent key by creating a workspace with "
            "pink_agentic_payments.create_sandbox_workspace() (no signup needed)."
        )
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url
    return PinkClient(key, **kwargs)


class _PinkToolBase(BaseTool):
    """Shared plumbing: lazily builds a PinkClient from an agent key or env var."""

    client: Optional[PinkClient] = Field(default=None, exclude=True)
    agent_key: Optional[str] = Field(default=None, exclude=True)
    base_url: Optional[str] = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}

    def _get_client(self) -> PinkClient:
        if self.client is not None:
            return self.client
        return _resolve_client(self.agent_key, self.base_url)


class RequestPaymentInput(BaseModel):
    amount: float = Field(description="Payment amount, in the given currency's smallest common unit (e.g. dollars for USD).")
    currency: str = Field(default="USD", description="Three-letter currency code, e.g. USD.")
    merchant: Optional[str] = Field(
        default=None,
        description="Payee name to pay, e.g. 'Blue Bottle Coffee'. Use this or payee_id, whichever you know.",
    )
    payee_id: Optional[str] = Field(
        default=None, description="Exact payee id from list_payees, if known. Preferred over merchant name when available."
    )
    purpose: Optional[str] = Field(default=None, description="Short free-text reason for the payment, e.g. 'office snacks'.")


class PinkRequestPaymentTool(_PinkToolBase):
    """Request a real sandbox payment, checked against the company's spending rules first."""

    name: str = "pink_request_payment"
    description: str = (
        "Request a payment from Pink Agentic AI Payments (sandbox preview, test money only). "
        "The company's rules (per-agent budget caps, allowed payees, human-approval thresholds) "
        "are checked before any money moves. Returns one of three decisions: "
        "'allowed' (a one-time sandbox payment credential was issued), "
        "'pending_human' (a human must approve this exact request before it can proceed), or "
        "'blocked' (this exact request will never be allowed; do not retry it unchanged)."
    )
    args_schema: Type[BaseModel] = RequestPaymentInput

    def _run(
        self,
        amount: float,
        currency: str = "USD",
        merchant: Optional[str] = None,
        payee_id: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> str:
        client = self._get_client()
        try:
            result = client.request_payment(
                amount=amount, currency=currency, payee_name=merchant, payee_id=payee_id, purpose=purpose
            )
            credential_type = (result.get("credential") or {}).get("type", "unknown")
            return (
                f"decision=allowed payment_id={result.get('payment_id')} "
                f"credential_type={credential_type}"
            )
        except PinkApprovalPending as e:
            who = e.payload.get("who", "a workspace owner")
            return (
                f"decision=pending_human payment_id={e.payload.get('payment_id')} "
                f"approver={who}. This request is on hold until a human approves or declines it; "
                "do not resubmit it."
            )
        except PinkPolicyDenied as e:
            rule = e.payload.get("rule", "a spending rule")
            return (
                f"decision=blocked payment_id={e.payload.get('payment_id')} "
                f"rule={rule!r}. This exact request will never be allowed; do not retry it unchanged."
            )
        except PinkAPIError as e:
            return f"error status={e.status_code} message={e}"


class CheckPolicyInput(BaseModel):
    amount: float = Field(description="Payment amount to dry-run, in the given currency.")
    currency: str = Field(default="USD", description="Three-letter currency code, e.g. USD.")
    merchant: Optional[str] = Field(default=None, description="Payee name to check, e.g. 'Blue Bottle Coffee'.")
    payee_id: Optional[str] = Field(default=None, description="Exact payee id from list_payees, if known.")
    purpose: Optional[str] = Field(default=None, description="Short free-text reason for the payment.")


class PinkCheckPolicyTool(_PinkToolBase):
    """Dry-run a payment against the company's spending rules without spending anything."""

    name: str = "pink_check_policy"
    description: str = (
        "Check, without spending anything, what decision a payment would get from Pink Agentic AI "
        "Payments' spending rules (sandbox preview). Use this before pink_request_payment to see "
        "whether an amount or payee would be allowed, blocked, or need human approval, so the agent "
        "can explain the outcome or try a different amount/payee first."
    )
    args_schema: Type[BaseModel] = CheckPolicyInput

    def _run(
        self,
        amount: float,
        currency: str = "USD",
        merchant: Optional[str] = None,
        payee_id: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> str:
        client = self._get_client()
        try:
            result = client.check_policy(
                amount=amount, currency=currency, payee_name=merchant, payee_id=payee_id, purpose=purpose
            )
            return f"would_decision={result.get('decision')} reason={result.get('reason')}"
        except PinkAPIError as e:
            return f"error status={e.status_code} message={e}"


class GetBudgetInput(BaseModel):
    pass


class PinkGetBudgetTool(_PinkToolBase):
    """Get this agent's remaining budget and spend-to-date in the sandbox."""

    name: str = "pink_get_budget"
    description: str = (
        "Get this agent's current budget from Pink Agentic AI Payments (sandbox preview): the cap, "
        "amount already spent, and amount remaining. Use this before proposing a payment to check "
        "whether there's enough budget left."
    )
    args_schema: Type[BaseModel] = GetBudgetInput

    def _run(self) -> str:
        client = self._get_client()
        try:
            budget = client.get_budget()
            currency = (budget.get("vault") or {}).get("balances", {})
            currency_code = next(iter(currency), "USD")
            return (
                f"monthly_budget={budget.get('monthly_budget')} "
                f"spent_this_month={budget.get('spent_this_month')} "
                f"left_this_month={budget.get('left_this_month')} "
                f"single_payment_cap={budget.get('single_payment_cap')} "
                f"currency={currency_code}"
            )
        except PinkAPIError as e:
            return f"error status={e.status_code} message={e}"


class CheckPaymentStatusInput(BaseModel):
    payment_id: str = Field(description="The payment id returned by pink_request_payment, e.g. 'pay_abc123'.")


class PinkCheckPaymentStatusTool(_PinkToolBase):
    """Look up the current status of a previously requested payment, e.g. a pending_human hold."""

    name: str = "pink_check_payment_status"
    description: str = (
        "Look up the current status of a payment previously requested via pink_request_payment "
        "(sandbox preview). Useful for polling a 'pending_human' hold to see if a human has approved "
        "or declined it yet. Returns the decision and, once allowed, the credential type."
    )
    args_schema: Type[BaseModel] = CheckPaymentStatusInput

    def _run(self, payment_id: str) -> str:
        client = self._get_client()
        try:
            payment = client.get_payment(payment_id)
            credential_type = (payment.get("credential") or {}).get("type")
            # The sandbox reports a human-approved hold as decision="approved"
            # (distinct from the immediate, no-human-needed "allowed" a fresh
            # request_payment() call returns), observed live 2026-10-12.
            return (
                f"decision={payment.get('decision')} payment_id={payment_id} "
                f"credential_type={credential_type}"
            )
        except PinkAPIError as e:
            return f"error status={e.status_code} message={e}"
