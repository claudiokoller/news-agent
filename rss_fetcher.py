"""
news_agent/rss_fetcher.py
Lädt Artikel von RSS-Feeds und filtert relevante Inhalte.
"""

import feedparser
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ─── Quellen ─────────────────────────────────────────────────────────────────

FEEDS = [
    # Schweiz & Lokal
    {"url": "https://www.cash.ch/rss/news",                              "kategorie": "Schweiz", "name": "Cash.ch",      "link": "https://cash.ch"},
    {"url": "https://www.srf.ch/news/bnf/rss/1646",                      "kategorie": "Schweiz", "name": "SRF Wirtschaft","link": "https://srf.ch/news/wirtschaft"},
    {"url": "https://www.nzz.ch/wirtschaft.rss",                         "kategorie": "Schweiz", "name": "NZZ",          "link": "https://nzz.ch/wirtschaft"},
    # Makro & Wirtschaft
    {"url": "https://feeds.reuters.com/reuters/businessNews",            "kategorie": "Makro",   "name": "Reuters",      "link": "https://reuters.com/business"},
    {"url": "https://www.handelsblatt.com/contentexport/feed/top-themen","kategorie": "Makro",   "name": "Handelsblatt", "link": "https://handelsblatt.com"},
    {"url": "https://www.economist.com/finance-and-economics/rss.xml",   "kategorie": "Makro",   "name": "Economist",    "link": "https://economist.com/finance-and-economics"},
    # Märkte
    {"url": "https://feeds.bloomberg.com/markets/news.rss",              "kategorie": "Märkte",  "name": "Bloomberg",    "link": "https://bloomberg.com/markets"},
    {"url": "https://www.investing.com/rss/news.rss",                    "kategorie": "Märkte",  "name": "Investing",    "link": "https://investing.com/news"},
    # Bitcoin (nur BTC-spezifisch, kein Altcoin/Crypto-Noise)
    {"url": "https://bitcoinmagazine.com/.rss/full/",                    "kategorie": "Bitcoin", "name": "Bitcoin Magazine", "link": "https://bitcoinmagazine.com"},
    {"url": "https://cointelegraph.com/rss/tag/bitcoin",                 "kategorie": "Bitcoin", "name": "CoinTelegraph",    "link": "https://cointelegraph.com/tags/bitcoin"},
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/",           "kategorie": "Bitcoin", "name": "CoinDesk",         "link": "https://coindesk.com"},
]

# Max. Artikel pro Feed (verhindert zu viele Tokens in Claude)
MAX_PER_FEED   = 5
# Nur Artikel der letzten X Stunden
HOURS_BACK     = 20


@dataclass
class Article:
    titel:     str
    quelle:    str
    kategorie: str
    zusammenfassung: str
    url:       str
    datum:     str


def fetch_all_articles() -> list[Article]:
    """Holt Artikel von allen konfigurierten Feeds."""
    all_articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)

    for feed_cfg in FEEDS:
        try:
            articles = _fetch_feed(feed_cfg, cutoff)
            all_articles.extend(articles)
            logger.info(f"  {feed_cfg['name']}: {len(articles)} Artikel")
        except Exception as e:
            logger.warning(f"Feed-Fehler {feed_cfg['name']}: {e}")

    return all_articles


def _fetch_feed(feed_cfg: dict, cutoff: datetime) -> list[Article]:
    feed     = feedparser.parse(feed_cfg["url"])
    articles = []

    for entry in feed.entries[:MAX_PER_FEED * 2]:  # Mehr holen, dann filtern
        # Datum prüfen
        pub_date = _parse_date(entry)
        if pub_date and pub_date < cutoff:
            continue

        # Zusammenfassung extrahieren
        summary = (
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
            or ""
        )
        # HTML-Tags entfernen (simpel)
        summary = _strip_html(summary)[:500]

        articles.append(Article(
            titel          = entry.get("title", "")[:200],
            quelle         = feed_cfg["name"],
            kategorie      = feed_cfg["kategorie"],
            zusammenfassung = summary,
            url            = entry.get("link", ""),
            datum          = pub_date.strftime("%H:%M") if pub_date else "",
        ))

        if len(articles) >= MAX_PER_FEED:
            break

    return articles


def _parse_date(entry) -> datetime | None:
    """Parst published_parsed oder updated_parsed aus feedparser."""
    import time
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
            except Exception:
                pass
    return None


def _strip_html(text: str) -> str:
    """Entfernt HTML-Tags simpel via String-Replace."""
    import re
    return re.sub(r"<[^>]+>", "", text).strip()


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    articles = fetch_all_articles()
    print(f"\n📰 {len(articles)} Artikel gefunden:\n")
    for a in articles:
        print(f"  [{a.kategorie}] {a.quelle}: {a.titel[:70]}")
