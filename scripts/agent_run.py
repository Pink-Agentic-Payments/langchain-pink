"""One real LangGraph create_react_agent run through the PinkToolkit.

No LLM API key was available in this environment (checked OPENAI_API_KEY,
ANTHROPIC_API_KEY, GEMINI_API_KEY; none set), so per the task brief this
script does NOT call a real LLM. Instead it drives the actual
create_react_agent graph (real LangGraph state machine, real tool-call
dispatch, real PinkToolkit calls against the live sandbox) with
langchain_core's FakeMessagesListChatModel standing in for the model: a
scripted but genuine sequence of AIMessages with tool_calls, so this proves
the LangGraph <-> PinkToolkit wiring actually works end-to-end, not just
that the tools work in isolation (that's already covered by
tests/integration_tests). This is clearly NOT an LLM reasoning demo.
"""
import json
import uuid

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from pink_agentic_payments import create_sandbox_workspace

from langchain_pink import PinkToolkit


class ScriptedToolCallingChatModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel plus a no-op bind_tools, so create_react_agent
    (which calls bind_tools to attach the tool schemas) accepts it."""

    def bind_tools(self, tools, **kwargs):
        return self

workspace = create_sandbox_workspace(company="LangChain Pink Agent Run", template="startup")
print("workspace_id:", workspace["workspace_id"], "(test money only; see NOTES.md)")
agent_key = workspace["agents"][0]["key"]

toolkit = PinkToolkit(agent_key=agent_key)
tools = toolkit.get_tools()

call_id_1 = str(uuid.uuid4())
call_id_2 = str(uuid.uuid4())

scripted_responses = [
    AIMessage(
        content="",
        tool_calls=[
            {
                "name": "pink_check_policy",
                "args": {"amount": 50, "payee_id": "p_figma", "purpose": "design tool renewal"},
                "id": call_id_1,
            }
        ],
    ),
    AIMessage(
        content="",
        tool_calls=[
            {
                "name": "pink_request_payment",
                "args": {"amount": 50, "payee_id": "p_figma", "purpose": "design tool renewal"},
                "id": call_id_2,
            }
        ],
    ),
    AIMessage(content="Paid Figma $50 for the design tool renewal: it was allowed immediately."),
]

model = ScriptedToolCallingChatModel(responses=scripted_responses)
agent = create_react_agent(model, tools)

result = agent.invoke(
    {"messages": [HumanMessage(content="Check the policy for a $50 Figma renewal, then pay it if it's fine.")]}
)

print("\n=== Transcript ===")
for m in result["messages"]:
    kind = m.__class__.__name__
    content = m.content or getattr(m, "tool_calls", "")
    print(f"[{kind}] {content}")
