"""
news_agent/tg.py
Sendet das Briefing via Telegram.
Separater Bot / Chat vom Invoice Agent.
"""

import os
import logging
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
import html

logger = logging.getLogger(__name__)

# Eigener Bot für News (separater Chat vom Invoice Agent)
TELEGRAM_TOKEN   = os.environ["NEWS_TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["NEWS_TELEGRAM_CHAT_ID"]


TELEGRAM_MAX_LEN = 4000


def _split_message(text: str) -> list[str]:
    """Splits text into Telegram-safe chunks at newline boundaries."""
    if len(text) <= TELEGRAM_MAX_LEN:
        return [text]
    parts = []
    while len(text) > TELEGRAM_MAX_LEN:
        split_at = text.rfind("\n", 0, TELEGRAM_MAX_LEN)
        if split_at == -1:
            split_at = TELEGRAM_MAX_LEN
        parts.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        parts.append(text)
    return parts


async def send_briefing(text: str):
    """Sendet das fertige Briefing via Telegram (splittet bei Bedarf)."""
    bot = Bot(token=TELEGRAM_TOKEN)
    parts = _split_message(text)

    for part in parts:
        try:
            await bot.send_message(
                chat_id                  = TELEGRAM_CHAT_ID,
                text                     = part,
                parse_mode               = ParseMode.HTML,
                disable_web_page_preview = True,
            )
        except Exception as e:
            logger.warning(f"HTML fehlgeschlagen, sende als plain text: {e}")
            await bot.send_message(
                chat_id = TELEGRAM_CHAT_ID,
                text    = part,
            )

    logger.info(f"✅ Telegram Nachricht gesendet ({len(parts)} Teil(e))")


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_text = (
        "☀️ *Wirtschafts-Briefing – Test*\n\n"
        "🌍 *MAKRO*\n"
        "• SNB senkt Leitzins auf 0.25%\n\n"
        "₿ *BITCOIN & CRYPTO*\n"
        "• Bitcoin bei $90k – neues Jahreshoch"
    )

    asyncio.run(send_briefing(test_text))
