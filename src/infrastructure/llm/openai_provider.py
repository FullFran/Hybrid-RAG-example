import json
from typing import AsyncIterator, List

import openai

from src.core.interfaces.llm import ILLMProvider, ToolCall, ToolResponse


class OpenAILLMProvider(ILLMProvider):
    """OpenAI implementation of the LLM provider interface with tool support."""

    def __init__(self, api_key: str, model: str, base_url: str):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def generate_response(
        self, system_prompt: str, user_prompt: str, stream: bool = False
    ) -> AsyncIterator[str] | str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if stream:
            return self._stream_response(messages)
        else:
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages
            )
            return response.choices[0].message.content

    async def _stream_response(self, messages: List[dict]) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model, messages=messages, stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def supports_tools(self) -> bool:
        """OpenAI supports function calling."""
        return True

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
    ) -> ToolResponse:
        """Generate a response with OpenAI function calling.

        The LLM will decide whether to call a tool or respond directly.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",  # Let the model decide
        )

        choice = response.choices[0]
        message = choice.message

        # Check if the model wants to call tools
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                # Parse the arguments JSON string
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                tool_calls.append(ToolCall(name=tc.function.name, arguments=args))
            return ToolResponse(content=None, tool_calls=tool_calls)
        else:
            # Model responded directly without calling tools
            return ToolResponse(content=message.content, tool_calls=[])
