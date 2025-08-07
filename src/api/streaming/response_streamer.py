import asyncio
from typing import AsyncGenerator

class ResponseStreamer:
    """
    Manages the streaming of responses, typically from an AI model.
    This class acts as an intermediary, converting model outputs into
    a streamable format for WebSocket or other streaming protocols.
    """
    def __init__(self):
        pass

    async def stream_tokens(self, async_generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """
        Takes an async generator (e.g., from a Pydantic AI model) and yields
        each token as it becomes available.
        """
        async for token in async_generator:
            yield token

    async def stream_json_data(self, async_generator: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
        """
        Takes an async generator yielding dictionaries and converts each dictionary
        into a JSON string before yielding it.
        """
        async for data in async_generator:
            yield json.dumps(data)

    # You can add more streaming methods here as needed, e.g., for different data formats
