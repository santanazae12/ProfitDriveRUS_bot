import json
import os
from openai import AsyncOpenAI

SYSTEM = """You are CarFlip AI, an expert vehicle-flipping assistant.
Be concise, practical, and honest. Never claim a vehicle is safe without an in-person inspection.
Do not invent VIN history, confirmed sale data, part compatibility, recalls, torque specs, or prices.
When information is missing, state assumptions. Give estimated ranges, risk flags, a profit calculation,
a recommended maximum purchase price, and a BUY / NEGOTIATE / SKIP decision.
For repairs, include safety warnings and tell the user when professional diagnosis is required.
Return clean Telegram-friendly text with short sections and no markdown tables."""

class AI:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def ask(self, prompt: str) -> str:
        if not self.client:
            return (
                "⚠️ OPENAI_API_KEY is not connected yet.\n\n"
                "Add it in your hosting Variables, then restart the bot."
            )
        response = await self.client.responses.create(
            model=self.model,
            instructions=SYSTEM,
            input=prompt,
        )
        return response.output_text.strip()
