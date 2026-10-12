"""LangChain standard unit tests (langchain_tests.unit_tests.ToolsUnitTests)."""
from typing import Type

from langchain_core.tools import BaseTool
from langchain_tests.unit_tests import ToolsUnitTests

from langchain_pink.tools import (
    PinkCheckPaymentStatusTool,
    PinkCheckPolicyTool,
    PinkGetBudgetTool,
    PinkRequestPaymentTool,
)


class TestPinkRequestPaymentToolStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        return PinkRequestPaymentTool

    @property
    def tool_constructor_params(self) -> dict:
        return {"agent_key": "pk_sandbox_agent_fake_for_unit_tests"}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"amount": 5, "currency": "USD", "merchant": "Test Payee", "purpose": "unit test"}


class TestPinkCheckPolicyToolStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        return PinkCheckPolicyTool

    @property
    def tool_constructor_params(self) -> dict:
        return {"agent_key": "pk_sandbox_agent_fake_for_unit_tests"}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"amount": 5, "currency": "USD", "merchant": "Test Payee", "purpose": "unit test"}


class TestPinkGetBudgetToolStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        return PinkGetBudgetTool

    @property
    def tool_constructor_params(self) -> dict:
        return {"agent_key": "pk_sandbox_agent_fake_for_unit_tests"}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {}


class TestPinkCheckPaymentStatusToolStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        return PinkCheckPaymentStatusTool

    @property
    def tool_constructor_params(self) -> dict:
        return {"agent_key": "pk_sandbox_agent_fake_for_unit_tests"}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"payment_id": "pay_fake123"}
