from typing import AsyncIterator, List

import openai

from src.core.interfaces.llm import ILLMProvider


class OpenAILLMProvider(ILLMProvider):
    """OpenAI implementation of the LLM provider interface."""

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
