"""
news-agent/summarizer.py
Nutzt Claude API um die gesammelten Artikel zu einem
kompakten Wirtschafts-Briefing zusammenzufassen.
"""

import os
import re
import logging
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from rss_fetcher import Article

logger = logging.getLogger(__name__)

load_dotenv()


def _client() -> Anthropic:
    """Client erst beim Aufruf erzeugen - so bleibt das Modul ohne
    gesetzten API-Key importierbar (z.B. in den Tests)."""
    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """
Du bist ein freundlicher, gut gelaunter Wirtschaftsjournalist aus der Schweiz. Du schreibst jeden Morgen ein persönliches Briefing für einen jungen Schweizer Investor.

Regeln:
- Beginne mit einem kurzen, lockeren Begrüssungssatz (1 Zeile) – variiere täglich, darf humorvoll oder überraschend sein
- Fasse die wichtigsten Nachrichten zusammen, gruppiert nach Sektionen – maximal 2 Bulletpoints pro Sektion, insgesamt max. 8 Bulletpoints
- Wichtig: Die gesamte Ausgabe darf 3500 Zeichen nicht überschreiten (Telegram-Limit)
- Sprache: Deutsch (Schweizer Schreibweise: kein ß, immer ss – z.B. «Strasse», «heissen», «grösser»)
- Ton: locker, klar, informativ – nicht trocken
- Zahlen und Fakten wo verfügbar einbauen (%, Preise, Namen)
- Keine Meinungen, keine Empfehlungen
- Jeder Bulletpoint max. 1–2 Sätze, danach den direkten Artikel-Link anhängen (ARTIKEL_URL aus den Daten verwenden, NICHT die Hauptseite): z.B. • SNB senkt Leitzins auf 0.25%. <a href="https://nzz.ch/wirtschaft/snb-artikel...">NZZ</a>
- Hebe wichtige Zahlen, Namen und Schlüsselbegriffe mit <b>fett</b> hervor (z.B. Prozentzahlen, Firmen, Währungsbeträge)
- Pro Quelle maximal 2 Bulletpoints – verschiedene Quellen sollen vertreten sein
- Falls eine Kategorie keine relevanten News hat, weglassen
- Keine separate Quellenliste am Schluss – die Links sind bereits inline bei jeder News
- "Daily Fun Fact" Sektion ganz am Schluss: 1 überraschende oder witzige Tatsache – täglich zufälliges Thema aus Wissenschaft, Geschichte, Antike, Natur, Sport, Technik, Sprache, Geografie usw. Nichts mit Wirtschaft oder Bitcoin. Beschrifte sie mit 💡 <b>Daily Fun Fact</b>

Ausgabe ist Telegram HTML. Verwende ausschließlich diese Tags: <b>, <i>, <a href="url">text</a>.
Wichtig: Alle URLs genau so übernehmen wie angegeben. Kein & in URLs – ersetze & durch &amp; falls nötig.
Keine Markdown-Syntax (kein *, kein _, kein [text](url)).

Format (exakt so, mit Leerzeilen zwischen Sektionen):
☀️ <b>Guten Morgen!</b>

[lockerer Begrüssungssatz]

<i>{datum}</i>

━━━━━━━━━━━━━━━

🇨🇭 <b>SCHWEIZ</b>

• [News.] <a href="url">Quelle</a>

🌍 <b>MAKRO</b>

• [News.] <a href="url">Quelle</a>

📈 <b>MÄRKTE</b>

• [News.] <a href="url">Quelle</a>

₿ <b>BITCOIN</b>

• [News.] <a href="url">Quelle</a>

💡 <b>Daily Fun Fact</b>

• [Überraschende Tatsache.]

━━━━━━━━━━━━━━━
[Lockerer, motivierender Abschlusssatz – kurz, persönlich, darf auch witzig sein.]
"""

USER_TEMPLATE = """
Hier sind die heutigen Artikel ({anzahl} total):

{artikel_text}

Erstelle das Briefing. Heutiges Datum: {datum}
"""


def summarize_articles(articles: list[Article]) -> str | None:
    """
    Lässt Claude die Artikel zu einem Briefing zusammenfassen.
    Gibt den fertigen Briefing-Text zurück.
    """
    if not articles:
        return None

    # Artikel als kompakten Text aufbereiten
    artikel_text = _format_articles(articles)
    datum        = datetime.now().strftime("%A, %d. %B %Y")

    prompt = USER_TEMPLATE.format(
        anzahl       = len(articles),
        artikel_text = artikel_text,
        datum        = datum,
    )

    try:
        response = _client().messages.create(
            model      = "claude-sonnet-5",
            # Grosszuegig: das Limit deckt Denk- und Textanteil ab. Abgerechnet
            # wird nur, was tatsaechlich erzeugt wird - ein hoher Wert kostet nichts.
            max_tokens = 16000,
            system     = SYSTEM_PROMPT,
            messages   = [{"role": "user", "content": prompt}],
        )

        if response.stop_reason == "max_tokens":
            logger.warning("max_tokens erreicht - Briefing ist abgeschnitten")

        briefing = _fix_html(_extract_text(response).strip())
        logger.info(f"Briefing generiert ({len(briefing)} Zeichen)")
        return briefing

    except Exception as e:
        logger.error(f"Claude API Fehler: {e}")
        return None


def _extract_text(response) -> str:
    """Holt den Text aus der Antwort.

    content[0] ist nicht zwingend der Text: Claude denkt bei Bedarf vor der
    Antwort, dann steht an erster Stelle ein ThinkingBlock. Darum den ersten
    echten Textblock suchen.
    """
    for block in response.content:
        if block.type == "text":
            return block.text
    raise ValueError("Antwort enthielt keinen Textblock")


def _fix_html(text: str) -> str:
    """Escaped bare & in URLs/text so Telegram HTML doesn't choke."""
    return re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)


def _format_articles(articles: list[Article]) -> str:
    """Formatiert Artikel als kompakten Text für den Prompt."""
    lines = []
    current_kategorie = None

    # Nach Kategorie sortieren
    for a in sorted(articles, key=lambda x: x.kategorie):
        if a.kategorie != current_kategorie:
            lines.append(f"\n## {a.kategorie}")
            current_kategorie = a.kategorie

        lines.append(
            f"- [{a.quelle}] {a.titel} | ARTIKEL_URL: {a.url}"
            + (f"\n  {a.zusammenfassung}" if a.zusammenfassung else "")
        )

    return "\n".join(lines)


# ─── Test ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from rss_fetcher import fetch_all_articles
    articles = fetch_all_articles()

    if not articles:
        print("Keine Artikel")
    else:
        briefing = summarize_articles(articles)
        print("\n" + "─" * 50)
        print(briefing)
        print("─" * 50)
