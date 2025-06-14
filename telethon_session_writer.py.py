import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

# Загружаем переменные из .env
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "session")  # fallback если SESSION_NAME не указан

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()
    print(f"✅ Сессия успешно сохранена как {session_name}.session")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
