"""LangChain tools for Pink Agentic AI Payments.

Pink Agentic AI Payments lets AI agents pay within spending rules a company
sets in advance (per-agent budgets, payee allow-lists, human-approval
thresholds). This package wraps the official ``pink-agentic-payments``
Python client as LangChain ``BaseTool`` objects so an agent built with
``langgraph`` or any other LangChain-compatible framework can request a
payment, check its budget, and check a payment's status as part of a tool
loop.

Sandbox preview: every tool here talks to the public Pink sandbox
(https://agentic-sandbox.pinkwallet.com), test money only. See
https://pinkwallet.com/agentic/developers/ for details.
"""
from .toolkit import PinkToolkit
from .tools import (
    PinkCheckPaymentStatusTool,
    PinkCheckPolicyTool,
    PinkGetBudgetTool,
    PinkRequestPaymentTool,
)

__version__ = "0.1.0"

__all__ = [
    "PinkToolkit",
    "PinkRequestPaymentTool",
    "PinkCheckPolicyTool",
    "PinkGetBudgetTool",
    "PinkCheckPaymentStatusTool",
    "__version__",
]
