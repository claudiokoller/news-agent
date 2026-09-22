"""
Unit-Tests für die Hilfsfunktionen, die ohne Netzwerk und ohne API-Keys
auskommen. Bewusst klein gehalten – getestet wird die Logik, die bei
unsauberem Feed-Input oder langen Briefings tatsächlich schiefgehen kann.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rss_fetcher import _strip_html


def test_strip_html_entfernt_tags():
    assert _strip_html("<p>Hallo <b>Welt</b></p>") == "Hallo Welt"


def test_strip_html_laesst_klartext_unveraendert():
    assert _strip_html("  SNB senkt Zins  ") == "SNB senkt Zins"


def test_fix_html_escaped_nacktes_ampersand():
    from summarizer import _fix_html
    assert _fix_html("Meier & Co") == "Meier &amp; Co"


def test_fix_html_laesst_bestehende_entities_in_ruhe():
    from summarizer import _fix_html
    assert _fix_html("<b>A &amp; B</b>") == "<b>A &amp; B</b>"


def test_split_message_laesst_kurze_nachricht_ganz():
    from tg import _split_message
    assert _split_message("kurz") == ["kurz"]


def test_split_message_teilt_an_zeilenumbruch():
    from tg import _split_message
    text = "\n".join(f"Zeile {i}" * 50 for i in range(20))
    parts = _split_message(text)
    assert len(parts) > 1
    assert all(len(p) <= 4000 for p in parts)
    assert "".join(p.replace("\n", "") for p in parts) == text.replace("\n", "")
