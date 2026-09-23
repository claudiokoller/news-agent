# News Agent

Sammelt jeden Morgen um 07:00 Wirtschaftsnachrichten aus 10 RSS-Feeds, lässt sie
von Claude zu einem Briefing zusammenfassen und schickt es per Telegram.
Läuft täglich per Cron auf einem kleinen Linux-Server.

[![Tests](https://github.com/claudiokoller/news-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/claudiokoller/news-agent/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Was der Agent macht

1. **Sammeln** – 10 RSS-Feeds aus vier Bereichen: Schweiz, Makro, Märkte, Bitcoin.
2. **Filtern** – nur Artikel der letzten 20 Stunden, höchstens 5 pro Quelle.
   Das hält den Prompt klein und die Kosten pro Lauf im Rappenbereich.
3. **Zusammenfassen** – ein einziger Claude-Aufruf priorisiert, kürzt und
   formatiert in einem Schritt.
4. **Senden** – das fertige Briefing geht per Telegram raus, mit Links zu den
   Originalartikeln.

## Beispiel

```
☀️ Guten Morgen!

Die Märkte sind wach, der Kaffee ist heiss – legen wir los.

🇨🇭 SCHWEIZ
• Die SNB belässt den Leitzins bei 0.25%. — NZZ

🌍 MAKRO
• Die EZB signalisiert eine längere Zinspause. — Handelsblatt

📈 MÄRKTE
• Der SMI schliesst 0.8% höher. — Bloomberg

💡 Daily Fun Fact
• Honig verdirbt nie – in ägyptischen Gräbern gefundene Töpfe
  waren nach 3000 Jahren noch geniessbar.
```

*(Beispiel mit erfundenen Zahlen.)*

## Architektur

```mermaid
flowchart LR
    CRON([Cron 07:00]) --> MAIN[main.py]
    MAIN --> RSS[rss_fetcher.py]
    RSS --> SUM[summarizer.py]
    SUM --> TG[tg.py]

    FEEDS[(10 RSS-Feeds)] -.-> RSS
    SUM <-.-> CLAUDE{{Claude API}}
    TG -.-> USER([Telegram])
```

Vier Schritte nacheinander – kein Server, keine Datenbank, kein dauerhaft
laufendes Programm. Cron startet das Skript, nach dem Versand beendet es sich
wieder.

Mehr Details: [docs/architecture.md](docs/architecture.md)

## Module

| Datei | Aufgabe |
|---|---|
| `main.py` | Ruft die drei Schritte nacheinander auf |
| `rss_fetcher.py` | Feeds laden und filtern (letzte 20 h, max. 5 pro Feed) |
| `summarizer.py` | Prompt bauen und Claude API aufrufen |
| `tg.py` | Versand via Telegram |

## Setup

```bash
git clone https://github.com/claudiokoller/news-agent.git
cd news-agent
pip install -r requirements.txt

cp .env.example .env    # API-Key und Telegram-Daten eintragen
python main.py
```

Braucht Python 3.10+, einen [Anthropic API-Key](https://console.anthropic.com)
und einen Telegram-Bot (via [@BotFather](https://t.me/BotFather)). Die drei
Zugangsdaten stehen in der `.env` – die Datei ist nie Teil des Repos.

Automatisch laufen lassen, täglich um 07:00 – per Cron:

```
0 7 * * * /usr/bin/python3 /pfad/zu/news-agent/main.py >> news-agent.log 2>&1
```

## Tests

```bash
pip install pytest && pytest
```

9 Tests, ohne Netzzugriff und ohne API-Key lauffähig.

## Designentscheide

- **Erst filtern, dann fragen.** Ohne Begrenzung landen schnell 100+ Artikel im
  Prompt. Zeitfenster und Limit pro Quelle halten die Kosten klein und
  verhindern, dass eine schreibfreudige Quelle das Briefing dominiert.
- **Jede Stufe darf ausfallen.** Feed nicht erreichbar → überspringen.
  API-Fehler → nichts senden. Telegram lehnt die Formatierung ab → nochmal als
  einfacher Text. Ein einzelner Fehler kostet nie das ganze Briefing.
- **Kein Gedächtnis nötig.** Statt zu speichern, welche Artikel schon im
  Briefing waren, schaut das Programm 20 Stunden zurück – bei einem täglichen
  Lauf reicht das und spart die ganze Datenbank.

Bekannte Grenzen: Dieselbe Meldung kann über zwei Quellen doppelt im Briefing
landen, und die Feeds werden nacheinander statt parallel abgerufen – bei zehn
Quellen fällt das nicht ins Gewicht.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
