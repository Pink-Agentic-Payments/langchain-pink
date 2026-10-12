# langchain-pink

**Pink Agentic AI Payments** lets AI agents pay within spending rules a company sets in advance: per-agent budgets, payee allow-lists, and human-approval thresholds. This package wraps the official [`pink-agentic-payments`](https://pypi.org/project/pink-agentic-payments/) Python client as LangChain tools, so a `langgraph` (or any LangChain-compatible) agent can request a payment, check its remaining budget, and poll a payment's status as part of its normal tool loop.

> **Sandbox preview.** Every tool here talks to the public Pink sandbox (`https://agentic-sandbox.pinkwallet.com`). It uses test money only — no real funds ever move. Workspaces and keys created in the sandbox can appear or disappear without notice; use it for development and demos, not production. See the [docs hub](https://pinkwallet.com/agentic/developers/) for production status.

## Install

```bash
pip install langchain-pink
```

Or install both packages straight from GitHub:

```bash
pip install "pink-agentic-payments @ git+https://github.com/Pink-Agentic-Payments/pink-agentic-payments-python" \
            "langchain-pink @ git+https://github.com/Pink-Agentic-Payments/langchain-pink"
```

## Quickstart

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from pink_agentic_payments import create_sandbox_workspace
from langchain_pink import PinkToolkit

# 1. Spin up a free sandbox workspace (no signup, test money only)
workspace = create_sandbox_workspace(company="My Test Co", template="startup")
agent_key = workspace["agents"][0]["key"]

# 2. Build the toolkit and hand it to an agent
toolkit = PinkToolkit(agent_key=agent_key)
agent = create_react_agent(ChatOpenAI(model="gpt-4o-mini"), toolkit.get_tools())

result = agent.invoke(
    {"messages": [("user", "Pay Figma $50 for our design tool renewal, check the budget first.")]}
)
print(result["messages"][-1].content)
```

`agent_key` can also be supplied via the `PINK_AGENT_API_KEY` environment variable instead of the constructor argument.

## Tools

| Tool | Wraps | Decision |
|---|---|---|
| `pink_request_payment` | `PinkClient.request_payment` | `allowed`, `pending_human`, or `blocked`, with the reason |
| `pink_check_policy` | `PinkClient.check_policy` | dry-run: `would_allow`, `would_ask`, or `would_block` — no spend |
| `pink_get_budget` | `PinkClient.get_budget` | this agent's monthly budget, spend, and single-payment cap |
| `pink_check_payment_status` | `PinkClient.get_payment` | poll a payment, e.g. a `pending_human` hold, by id |

Every tool maps 1:1 to a method already in the official `pink-agentic-payments` client — this package adds no new API surface, only LangChain `BaseTool` wrappers with Pydantic argument schemas for the LLM to read.

## Links

- Docs hub: https://pinkwallet.com/agentic/developers/
- Official Python client: https://pypi.org/project/pink-agentic-payments/
- Sandbox: https://agentic-sandbox.pinkwallet.com (REST + MCP at `/mcp`)

## Development

```bash
pip install -e ".[test]"
pytest tests/unit_tests          # no network
pytest tests/integration_tests   # hits the live sandbox, creates a workspace
```

## License

MIT, see `LICENSE`.
