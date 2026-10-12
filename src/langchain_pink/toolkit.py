"""PinkToolkit: all Pink Agentic AI Payments tools, sharing one agent key."""
from __future__ import annotations

from typing import List, Optional

from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit
from pink_agentic_payments import PinkClient

from .tools import (
    PinkCheckPaymentStatusTool,
    PinkCheckPolicyTool,
    PinkGetBudgetTool,
    PinkRequestPaymentTool,
)


class PinkToolkit(BaseToolkit):
    """Toolkit bundling every Pink Agentic AI Payments tool for one agent key.

    Sandbox preview (test money only). Get a free agent key with
    ``pink_agentic_payments.create_sandbox_workspace()`` (no signup needed),
    or set it in the ``PINK_AGENT_API_KEY`` environment variable and omit
    ``agent_key`` below.
    """

    agent_key: Optional[str] = None
    base_url: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}

    def get_tools(self) -> List[BaseTool]:
        shared = {"agent_key": self.agent_key, "base_url": self.base_url}
        return [
            PinkRequestPaymentTool(**shared),
            PinkCheckPolicyTool(**shared),
            PinkGetBudgetTool(**shared),
            PinkCheckPaymentStatusTool(**shared),
        ]
