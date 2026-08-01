"""Render docs/SPEAKING_SCRIPTS.md to a printable PDF.

The Markdown file is the single source of truth — it is what gets edited and
what teammates read on screen. This only renders it, so the two can never
disagree. Deliberately a small hand-rolled renderer rather than a Markdown
library: the input is one known document, and adding a dependency the night
before a final is not worth it.

    python scripts/md_to_pdf.py
    python scripts/md_to_pdf.py docs/FOOTAGE_SHOT_LIST.md
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle

from make_docs import INK, MUTED, NAVY, build, styles

ACCENT = colors.HexColor("#0e7490")
QUOTE_BG = colors.HexColor("#f1f5f9")
CALLOUT_BG = colors.HexColor("#fff7ed")

# A4 is 210mm wide; build() uses a 22mm margin each side, leaving 166mm.
# A flowable even slightly wider than the frame does not just overflow —
# reportlab page-breaks around it forever (a 619-page "13-page" document).
# Leave real slack.
USABLE_MM = 158


def esc(t):
    """Markdown inline -> reportlab inline markup."""
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', t)
    return t


def flush_quote(buf, S, out):
    """A blockquote is a SPOKEN line — render it as a tinted panel so a nervous
    presenter can find 'what do I actually say' at a glance."""
    if not buf:
        return
    body = "<br/><br/>".join(buf)
    is_stage = body.startswith("[") or body.startswith("<b>[")
    t = Table([[Paragraph(body, S["say"])]], colWidths=[USABLE_MM * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CALLOUT_BG if is_stage else QUOTE_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT),
    ]))
    out.append(t)
    out.append(Spacer(1, 5))
    buf.clear()


def flush_table(rows, S, out):
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    # NOTE: pad into a NEW name. Rebinding `rows` would make the `rows.clear()`
    # at the end clear the copy, leaving the caller's buffer full — the table
    # then re-emits, growing, on every subsequent line (a 13-page document
    # rendered as 631 pages).
    padded = [r + [""] * (ncol - len(r)) for r in rows]
    data = [[Paragraph(esc(c), S["td_h"] if i == 0 else S["td"]) for c in r]
            for i, r in enumerate(padded)]
    avail = USABLE_MM * mm
    # First column carries the question/label; give it more room in 2-col tables.
    widths = ([avail * 0.34] + [avail * 0.66] if ncol == 2
              else [avail / ncol] * ncol)
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7dee9")),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    out.append(t)
    out.append(Spacer(1, 7))
    rows.clear()


def render(md_path, pdf_path, subtitle):
    S = styles()
    S["say"] = ParagraphStyle("say", parent=S["body"], fontSize=10.4,
                              leading=15.5, textColor=INK, spaceAfter=0)
    S["td"] = ParagraphStyle("td", parent=S["body"], fontSize=8.6,
                             leading=12, spaceAfter=0)
    S["td_h"] = ParagraphStyle("tdh", parent=S["td"], textColor=colors.white,
                               fontName="Helvetica-Bold")
    S["h3"] = ParagraphStyle("h3", parent=S["h2"], fontSize=10.5,
                             textColor=MUTED)
    S["li"] = ParagraphStyle("li", parent=S["body"], leftIndent=10,
                             bulletIndent=2, spaceAfter=3)

    out = [Spacer(1, 6 * mm)]
    quote, tbl = [], []
    first_h1 = True

    for raw in open(md_path, encoding="utf-8").read().splitlines():
        line = raw.rstrip()

        if line.startswith(">"):
            flush_table(tbl, S, out)
            quote.append(esc(line.lstrip("> ").strip()) or "")
            continue
        flush_quote(quote, S, out)

        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):      # separator row
                continue
            tbl.append(cells)
            continue
        flush_table(tbl, S, out)

        if not line.strip() or set(line.strip()) <= set("-—"):
            continue

        if line.startswith("# "):
            if not first_h1:
                out.append(PageBreak())
            first_h1 = False
            out.append(Paragraph(esc(line[2:]), S["title"]))
        elif line.startswith("## "):
            out.append(KeepTogether([Paragraph(esc(line[3:]), S["h1"])]))
        elif line.startswith("### "):
            out.append(Paragraph(esc(line[4:]), S["h3"]))
        elif re.match(r"^\d+\.\s", line):
            n, rest = line.split(".", 1)
            out.append(Paragraph(esc(rest.strip()), S["li"], bulletText=n + "."))
        elif line.startswith("- "):
            out.append(Paragraph(esc(line[2:]), S["li"], bulletText="•"))
        else:
            out.append(Paragraph(esc(line), S["body"]))

    flush_quote(quote, S, out)
    flush_table(tbl, S, out)
    build(pdf_path, A4, out, subtitle, margin=22)


# The footer subtitle is per-document. Keyed on the file so a teammate running
# `python scripts/md_to_pdf.py docs/BUSINESS_PLAN.md` gets the right banner
# instead of every PDF in the repo claiming to be the speaking scripts.
SUBTITLES = {
    "SPEAKING_SCRIPTS": "Speaking Scripts  |  1 August 2026",
    "SPEAKING_SCRIPTS_ROUND2": "Speaking Scripts  |  Round 2",
    "BUSINESS_PLAN": "Business Plan  |  Round 2",
    "FOOTAGE_SHOT_LIST": "Footage Shot List",
}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "docs/SPEAKING_SCRIPTS.md"
    base = os.path.splitext(src)[0]
    stem = os.path.basename(base).upper()
    subtitle = SUBTITLES.get(stem, stem.replace("_", " ").title())

    # A PDF the user is reading is locked on Windows, and losing a completed
    # render to that is maddening the night before a pitch. Walk to the next
    # free name instead, and say so loudly enough that nobody presents the
    # stale copy by mistake.
    for i, dst in enumerate([base + ".pdf"]
                            + [f"{base}_v{n}.pdf" for n in range(2, 6)]):
        try:
            render(src, dst, subtitle)
        except PermissionError:
            continue
        if i:
            print(f"NOTE: {base}.pdf is open in a PDF reader - wrote {dst} "
                  f"instead. Close it and re-run to write the real file.")
        return
    raise SystemExit(f"every {base}*.pdf is locked - close your PDF reader")


if __name__ == "__main__":
    main()
