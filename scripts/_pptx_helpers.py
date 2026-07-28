"""Generate the PowerPoint deck (docs/PRESENTATION.pptx).

Widescreen 16:9, dark theme matching the dashboard. Every image is the
system's own annotated output and every figure is a measured result.

    python scripts/make_pptx.py
"""
import os

from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
EV = os.path.join(ROOT, "docs", "DEMO_EVIDENCE")

W, H = Inches(13.333), Inches(7.5)          # 16:9
NAVY = RGBColor(0x0B, 0x14, 0x28)
PANEL = RGBColor(0x11, 0x1E, 0x3D)
CYAN = RGBColor(0x22, 0xD3, 0xEE)
WHITE = RGBColor(0xF2, 0xF6, 0xFF)
MUTED = RGBColor(0x9F, 0xB3, 0xD1)
GOLD = RGBColor(0xFF, 0xC7, 0x4D)
GREEN = RGBColor(0x4A, 0xDE, 0x80)


def bg(slide, colour=NAVY):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = colour


def box(slide, x, y, w, h, text, size=18, colour=WHITE, bold=False,
        align=PP_ALIGN.LEFT, font="Segoe UI", space=6):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        # inline **bold** segments
        for j, seg in enumerate(str(line).split("**")):
            if not seg:
                continue
            r = p.add_run()
            r.text = seg
            r.font.size = Pt(size)
            r.font.name = font
            r.font.color.rgb = colour
            r.font.bold = bold or (j % 2 == 1)
    return tb


def accent_bar(slide):
    s = slide.shapes.add_shape(1, 0, 0, W, Inches(0.09))
    s.fill.solid()
    s.fill.fore_color.rgb = CYAN
    s.line.fill.background()
    s.shadow.inherit = False


def picture(slide, name, x, y, max_w, max_h):
    """Place an image scaled to fit the given box, centred horizontally."""
    path = os.path.join(EV, name)
    if not os.path.exists(path):
        return None
    iw, ih = PILImage.open(path).size
    scale = min(max_w / iw, max_h / ih)
    w, h = int(iw * scale), int(ih * scale)
    return slide.shapes.add_picture(path, x + int((max_w - w) / 2), y,
                                    width=w, height=h)


def header(slide, title, kicker=None):
    accent_bar(slide)
    if kicker:
        box(slide, Inches(0.7), Inches(0.42), Inches(11), Inches(0.4),
            kicker, size=13, colour=CYAN, bold=True)
    box(slide, Inches(0.7), Inches(0.78), Inches(12), Inches(1.0),
        title, size=34, colour=WHITE, bold=True)


def stat(slide, x, y, value, label, colour=GOLD, w=Inches(2.9)):
    card = slide.shapes.add_shape(1, x, y, w, Inches(1.35))
    card.fill.solid()
    card.fill.fore_color.rgb = PANEL
    card.line.color.rgb = RGBColor(0x29, 0x4A, 0x8F)
    card.shadow.inherit = False
    box(slide, x, y + Inches(0.14), w, Inches(0.6), value, size=30,
        colour=colour, bold=True, align=PP_ALIGN.CENTER)
    box(slide, x, y + Inches(0.78), w, Inches(0.5), label, size=11.5,
        colour=MUTED, align=PP_ALIGN.CENTER)


