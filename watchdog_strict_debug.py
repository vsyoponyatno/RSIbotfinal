import os
import yaml
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# ===================== ЛОГИ =====================
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===================== ЗАГРУЗКА .ENV =====================
load_dotenv()

def get_env_var(name, required=True):
    value = os.getenv(name)
    if required and (value is None or value.strip() == ""):
        logger.critical(f"Переменная {name} не найдена в .env")
        raise SystemExit(f"❌ Обязательная переменная {name} отсутствует")
    return value

try:
    api_id = int(get_env_var("API_ID"))
    api_hash = get_env_var("API_HASH")
    session_name = get_env_var("SESSION_NAME")
    target_chat_id = int(get_env_var("TARGET_CHAT_ID"))
except Exception as e:
    logger.critical(f"Ошибка при чтении .env: {e}")
    raise SystemExit("❌ Остановка — проверь .env")

# ===================== ЗАГРУЗКА KEYWORDS =====================
try:
    with open("keywords.yaml", "r", encoding="utf-8") as f:
        keywords = yaml.safe_load(f)
    if not isinstance(keywords, dict):
        raise ValueError("keywords.yaml должен быть словарём категорий")
except Exception as e:
    logger.critical(f"Ошибка загрузки keywords.yaml: {e}")
    raise SystemExit("❌ Остановка — проверь файл keywords.yaml")

# ===================== ИНИЦИАЛИЗАЦИЯ КЛИЕНТА =====================
client = TelegramClient(session_name, api_id, api_hash)
me = None

# ===================== ФУНКЦИЯ РИСКА =====================
def calculate_risk(text):
    matches = []
    for category, keys in keywords.items():
        if not keys:
            continue
        for key in keys:
            if key.lower() in text.lower():
                matches.append(category)
                break

    level = "🚫"
    if len(matches) >= 3:
        level = "🔴"
    elif len(matches) == 2:
        level = "🟠"
    elif len(matches) == 1:
        level = "🟢"

    return level, matches

# ===================== ХЕНДЛЕР =====================
@client.on(events.NewMessage)
async def handler(event):
    global me
    try:
        msg = event.message
        if not msg or not msg.sender_id:
            return

        if msg.sender_id == me.id:
            logger.debug("⏩ Пропущено: сообщение от самого бота")
            return

        sender = await event.get_sender()
        chat = await event.get_chat()

        chat_type = (
            "Личка" if getattr(chat, "broadcast", False) is False and getattr(chat, "megagroup", False) is False
            else "Канал" if getattr(chat, "broadcast", False)
            else "Группа"
        )
        chat_name = getattr(chat, "title", "") or getattr(sender, "username", "") or f"ID {chat.id}"

        logger.debug(f"📩 Новое сообщение из [{chat_type}] {chat_name}")

        text = msg.message or ""
        level, categories = calculate_risk(text)

        if level == "🚫":
            return

        # Построение ссылки на сообщение
        link = None
        try:
            if hasattr(chat, 'username') and chat.username:
                link = f"https://t.me/{chat.username}/{msg.id}"
            elif hasattr(chat, 'id') and str(chat.id).startswith("-100"):
                link = f"https://t.me/c/{str(chat.id)[4:]}/{msg.id}"
        except Exception as e:
            logger.warning(f"⚠️ Не удалось построить ссылку: {e}")

        # Формирование сообщения
        formatted = f"{level} {', '.join(categories)}\n\n{text[:1000]}"
        if link:
            formatted += f"\n\n🔗 [Источник]({link})"

        # Отправка текста
        await client.send_message(target_chat_id, formatted, link_preview=False)

        # Медиа
        if msg.media and isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)):
            await client.send_file(target_chat_id, msg.media)

        logger.info(f"🚨 Сообщение обработано: {chat_type} / {chat_name}")
    except Exception as e:
        logger.exception(f"❌ Ошибка в обработчике: {e}")

# ===================== ПИНГ-ФУНКЦИЯ =====================
async def heartbeat():
    while True:
        logger.debug("💓 Heartbeat: бот жив.")
        await asyncio.sleep(60)

# ===================== ЗАПУСК =====================
async def main():
    global me
    await client.start()
    logger.info("🟢 Клиент успешно стартовал")

    if not await client.is_user_authorized():
        logger.critical("❌ Клиент не авторизован! Проверь session.")
        raise SystemExit("❌ Бот остановлен: требуется повторная авторизация.")

    me = await client.get_me()
    await client.send_message(target_chat_id, "🟢 Бот успешно запущен. Мониторинг включен.")
    logger.info(f"🟢 Бот авторизован как {me.username or me.first_name}")

    asyncio.create_task(heartbeat())  # <- добавлено

    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен вручную.")
    except Exception as e:
        logger.exception(f"❌ Фатальная ошибка при запуске: {e}")
