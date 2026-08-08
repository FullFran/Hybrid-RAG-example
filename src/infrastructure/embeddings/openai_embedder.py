import openai

from src.core.interfaces.embedder import IEmbedder


class OpenAIEmbedder(IEmbedder):
    """OpenAI implementation of the embedder interface."""

    def __init__(self, api_key: str, model: str, base_url: str):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def get_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self.client.embeddings.create(model=self.model, input=texts)
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]
