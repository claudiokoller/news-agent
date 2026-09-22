# 📰 News Agent

Ein kleiner Python-Agent, der jeden Morgen um 07:00 die Wirtschaftsnachrichten aus
11 RSS-Feeds einsammelt, sie von **Claude** zu einem kompakten Briefing verdichten
lässt und das Ergebnis per **Telegram** zustellt.

Statt zehn News-Apps durchzuscrollen: eine Nachricht, 60 Sekunden Lesezeit, mit
Direktlinks zu den Originalartikeln.

> Entstanden als persönliches Wochenend-Projekt und seither täglich im Einsatz.

---

## Was er macht

- **11 Quellen**, gruppiert in vier Sektionen – Schweiz (NZZ, SRF, Cash), Makro
  (Reuters, Handelsblatt, Economist), Märkte (Bloomberg, Investing) und Bitcoin.
- **Zeitfenster-Filter:** nur Artikel der letzten 20 Stunden, max. 5 pro Feed.
  Hält den Prompt klein und die Kosten pro Lauf im Rappenbereich.
- **Ein LLM-Call pro Tag:** Claude priorisiert, kürzt und formatiert in einem Schritt.
- **Telegram-HTML** mit Inline-Quellenlinks, automatischem Splitting langer
  Nachrichten und Plain-Text-Fallback.
- **Fehlertolerant:** ein nicht erreichbarer Feed kippt nie den ganzen Lauf.

## Beispiel-Ausgabe

```
☀️ Guten Morgen!

Die Märkte sind wach, der Kaffee ist heiss – legen wir los.

Montag, 22. September 2026
━━━━━━━━━━━━━━━

🇨🇭 SCHWEIZ
• Die SNB belässt den Leitzins bei 0.25% und verweist auf die
  abgeschwächte Teuerung. — NZZ
• Der Pharmakonzern meldet ein Umsatzplus von 6% im dritten
  Quartal. — Cash.ch

🌍 MAKRO
• Die EZB signalisiert eine längere Zinspause. — Reuters

📈 MÄRKTE
• Der SMI schliesst 0.8% höher, getrieben von Finanzwerten. — Bloomberg

💡 Daily Fun Fact
• Honig verdirbt nie – in ägyptischen Gräbern gefundene Töpfe
  waren nach 3000 Jahren noch geniessbar.

━━━━━━━━━━━━━━━
Guten Start in die Woche!
```

*(Beispiel mit erfundenen Zahlen.)*

## Architektur

```mermaid
flowchart LR
    CRON([Cron 07:00]) --> MAIN[main.py]
    MAIN --> RSS[rss_fetcher.py]
    RSS --> SUM[summarizer.py]
    SUM --> TG[tg.py]

    FEEDS[(11 RSS-Feeds)] -.-> RSS
    SUM <-.-> CLAUDE{{Claude API}}
    TG -.-> USER([Telegram])
```

Eine lineare Pipeline ohne Server, ohne Datenbank, ohne laufenden Prozess – Cron
startet das Skript, nach dem Versand beendet es sich wieder.

📄 **[Ausführliche Architektur, Ablauf und Designentscheidungen →](docs/architecture.md)**

## Projektstruktur

```
news_agent/
├── main.py           # Orchestrierung der drei Schritte
├── rss_fetcher.py    # Feeds laden, filtern, als Article-Dataclass normalisieren
├── summarizer.py     # Prompt bauen, Claude API, Telegram-HTML nachbessern
├── tg.py             # Versand inkl. Splitting und Fallback
├── tests/            # Unit-Tests für die Hilfsfunktionen
└── docs/             # Architekturdokumentation
```

## Setup

```bash
git clone https://github.com/claudiokoller/news_agent.git
cd news_agent

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env    # und die drei Werte eintragen
python main.py
```

### Benötigte Zugangsdaten

| Variable | Woher |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `NEWS_TELEGRAM_TOKEN` | Bot bei [@BotFather](https://t.me/BotFather) erstellen |
| `NEWS_TELEGRAM_CHAT_ID` | via [@userinfobot](https://t.me/userinfobot) auslesen |

Alle drei liegen in der lokalen `.env` – die Datei ist bewusst nie Teil des Repos.

### Module einzeln testen

Jedes Modul hat einen eigenen Einstiegspunkt, praktisch beim Entwickeln:

```bash
python rss_fetcher.py   # zeigt nur die gefundenen Artikel
python summarizer.py    # baut das Briefing, sendet es aber nicht
python tg.py            # schickt eine Testnachricht
```

## Täglicher Betrieb

Ein Crontab-Eintrag genügt:

```cron
0 7 * * * /usr/bin/python3 /pfad/zu/news_agent/main.py >> /var/log/news_agent.log 2>&1
```

## Tests

```bash
pip install pytest
pytest
```

Getestet sind die Funktionen, die ohne Netzwerk auskommen: HTML-Stripping,
Entity-Escaping und das Nachrichten-Splitting.

## Konfiguration anpassen

| Was | Wo |
|---|---|
| Quellen hinzufügen / entfernen | `FEEDS` in `rss_fetcher.py` |
| Zeitfenster und Artikel pro Feed | `HOURS_BACK`, `MAX_PER_FEED` in `rss_fetcher.py` |
| Ton, Sprache, Sektionen, Länge | `SYSTEM_PROMPT` in `summarizer.py` |

## Tech-Stack

Python 3.10+ · [feedparser](https://pypi.org/project/feedparser/) ·
[anthropic](https://pypi.org/project/anthropic/) ·
[python-telegram-bot](https://python-telegram-bot.org/) ·
[python-dotenv](https://pypi.org/project/python-dotenv/)

## Lizenz

[MIT](LICENSE) – gerne kopieren, anpassen und selbst laufen lassen.
