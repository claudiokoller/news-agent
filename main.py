"""
news_agent/main.py
Tägliches Wirtschafts-Briefing via Telegram.
Läuft jeden Morgen um 07:00 via Cronjob.

Crontab:
0 7 * * * /usr/bin/python3 /home/user/news_agent/main.py >> /var/log/news_agent.log 2>&1
"""

import asyncio
import logging
from rss_fetcher import fetch_all_articles
from summarizer  import summarize_articles
from tg          import send_briefing

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def run():
    logger.info("News Agent gestartet")

    # 1. Artikel von allen Quellen holen
    articles = fetch_all_articles()
    if not articles:
        logger.warning("Keine Artikel gefunden")
        return

    logger.info(f"{len(articles)} Artikel gesammelt")

    # 2. Claude fasst zusammen
    briefing = summarize_articles(articles)
    if not briefing:
        logger.error("Zusammenfassung fehlgeschlagen")
        return

    # 3. Via Telegram senden
    await send_briefing(briefing)
    logger.info("Briefing gesendet")


if __name__ == "__main__":
    asyncio.run(run())
