import re

from sqlalchemy.orm import Session

from app.agent.schemas import AgentRequest, AgentResponse, AgentToolResult
from app.agent.tools.calculator import calculator_tool
from app.agent.tools.current_time import current_time_tool
from app.agent.tools.document_search import document_search_tool
from app.ai.gateway import ai_gateway
from app.core.config import settings
from app.database.models import User


class EVUAgent:
    """Step 7 agent loop.

    The planner is deterministic for reliability during early development.
    Later steps can replace `plan()` with model-native tool/function calling
    without changing the API contract or the tool implementations.
    """

    _TIME_WORDS = ("time", "date", "utc", "today", "current time")
    _MATH_HINTS = (
        "calculate",
        "calculator",
        "solve",
        "what is",
        "how much",
        "sum",
        "multiply",
        "divide",
        "minus",
        "plus",
    )

    def plan(self, message: str, request: AgentRequest) -> list[str]:
        text = message.lower()
        tools: list[str] = []

        if request.use_rag:
            tools.append("document_search")

        has_expression = calculator_tool.extract_expression(message) is not None
        if has_expression and any(hint in text for hint in self._MATH_HINTS):
            tools.append("calculator")

        if any(word in text for word in self._TIME_WORDS):
            tools.append("current_time")

        # Preserve order and enforce the configured step limit.
        unique = list(dict.fromkeys(tools))
        return unique[: min(request.max_steps, settings.AGENT_MAX_STEPS)]

    async def run(
        self,
        request: AgentRequest,
        user: User,
        db: Session,
    ) -> AgentResponse:
        if not settings.AGENT_ENABLED:
            raise ValueError("Agent mode is disabled by server configuration.")

        planned_tools = self.plan(request.message, request)
        steps: list[AgentToolResult] = []
        sources = []
        context_blocks: list[str] = []

        for step_number, tool_name in enumerate(planned_tools, start=1):
            if tool_name == "document_search":
                result, tool_sources = await document_search_tool.run(
                    user.id, request.message, db
                )
                sources.extend(tool_sources)
            elif tool_name == "calculator":
                result = calculator_tool.run(request.message)
            elif tool_name == "current_time":
                result = current_time_tool.run(request.message)
            else:
                continue

            output = result.output[: settings.AGENT_MAX_TOOL_OUTPUT_CHARS]
            steps.append(
                AgentToolResult(
                    step=step_number,
                    tool=result.name,
                    input=result.input,
                    output=output,
                    success=result.success,
                )
            )
            if result.success:
                context_blocks.append(
                    f"TOOL: {result.name}\nINPUT: {result.input}\nRESULT:\n{output}"
                )

        system = (
            "You are EVU, an intelligent AI agent. Answer the user clearly and honestly. "
            "You may use the tool results below as evidence. Do not claim a tool result "
            "that is not present. If uploaded-document context is insufficient, say so."
        )
        if context_blocks:
            system += "\n\nAGENT TOOL RESULTS:\n" + "\n\n".join(context_blocks)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": request.message},
        ]

        try:
            response = await ai_gateway.generate(
                messages,
                request.provider,
                request.model,
            )
        except Exception as exc:
            # The agent can still return deterministic tool output for local
            # testing when no provider API key is configured.
            if steps:
                response = (
                    "EVU completed the available agent tools, but no configured AI "
                    f"provider could synthesize the final answer: {exc}\n\n"
                    + "\n\n".join(
                        f"{item.tool}: {item.output}" for item in steps
                    )
                )
            else:
                raise

        return AgentResponse(
            response=response,
            provider=request.provider,
            model=request.model,
            agent_used=True,
            rag_used=any(item.tool == "document_search" and item.success for item in steps),
            steps=steps,
            sources=sources,
        )


evu_agent = EVUAgent()