---
name: ai-orchestration-patterns
description: Apply AI orchestration patterns (routing, tool use, ReAct, fallbacks) to design reliable agent flows.
license: MIT
metadata:
  author: OpenCode
  version: "1.0"
---

# AI Orchestration Patterns

## When to use
- Designing agent flows, tool calling, or multi-step reasoning.
- Adding fallbacks, routing, or safety checks for LLM behavior.
- Improving observability and determinism of agent outcomes.

## Core guidance
- Separate decisioning from execution (planner vs. tool runner).
- Prefer explicit tool schemas and clear system instructions.
- Add guardrails: timeouts, max steps, and safe fallbacks.
- Log decisions with enough context for debugging.

## Do
- Keep tool routing in services (not endpoints).
- Define tool schemas close to the agent logic in `src/services/`.
- Add conservative fallbacks when tool support is missing.

## Don't
- Let LLMs call tools without validation of arguments.
- Mix orchestration logic into `src/endpoints/`.
- Skip logging of tool calls, queries, and chosen paths.

## Anti-patterns seen
- Hidden state in scratchpads without logging.
- Tool selection coupled to provider-specific formats.
- Unlimited loops without `max_steps` or timeouts.

## Repo anchors
- `src/services/agent_service.py`
- `src/services/rag_service.py`
- `src/services/context_builder.py`

## References
- https://the-amazing-gentleman-programming-book.vercel.app/es/book/Chapter19_AI-Orchestration-Patterns
