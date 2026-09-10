#!/usr/bin/env python3
"""
Creates SIH_Hackathon_Presentation_6Slides.pptx
Replicates the SIH26104--Presentation-Format template layout/style
for our SIH26106 email forensic platform topic.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Template colors ────────────────────────────────────────────────────────────
NAVY      = RGBColor(0x1F, 0x49, 0x7D)   # primary dark blue
GREEN     = RGBColor(0x00, 0xBF, 0x15)
DGREEN    = RGBColor(0x01, 0x6C, 0x0D)
ORANGE    = RGBColor(0xF2, 0x67, 0x20)
BLUE      = RGBColor(0x00, 0x70, 0xC0)
LBLUE     = RGBColor(0xDB, 0xE6, 0xF1)
LBLUE2    = RGBColor(0xDD, 0xEA, 0xF4)
YELLOW    = RGBColor(0xFF, 0xEC, 0x57)
CYAN      = RGBColor(0x00, 0xFF, 0xFF)
CRIMSON   = RGBColor(0xC0, 0x00, 0x00)
RED       = RGBColor(0xFF, 0x00, 0x00)
BLACK     = RGBColor(0x00, 0x00, 0x00)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
GRAY      = RGBColor(0x40, 0x40, 0x40)

F_TNR   = "Times New Roman"
F_GAR   = "Garamond"
F_ARIAL = "Arial"

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
SF = 108.0  # PDF 1440x810 -> inches scale factor

def X(u): return Inches(u / SF)
def Y(u): return Inches(u / SF)
def W2(u): return Inches(u / SF)

# ── helpers ────────────────────────────────────────────────────────────────────
def white_bg(slide):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

def txt(slide, x, y, w, h, text, size=18, color=BLACK, bold=False, italic=False,
        align=PP_ALIGN.LEFT, font=F_TNR, anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = slide.shapes.add_textbox(X(x), Y(y), W2(w), Y(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ln
        p.alignment = align
        p.font.size = Pt(size)
        p.font.name = font
        p.font.bold = bold
        p.font.italic = italic
        p.font.color.rgb = color
        p.space_before = Pt(0)
        p.space_after = Pt(0)
    return tb

def box(slide, x, y, w, h, fill=None, line=None, line_w=1.0, r=0.05):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, X(x), Y(y), W2(w), Y(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    try:
        shp.adjustments[0] = r
    except Exception:
        pass
    shp.shadow.inherit = False
    return shp

def circle(slide, x, y, d, fill, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, X(x), Y(y), W2(d), W2(d))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1.2)
    shp.shadow.inherit = False
    return shp

def footer(slide, page_num):
    box(slide, 0, 767, 1440, 43, fill=NAVY, line=None)
    txt(slide, 0, 768, 1440, 38, "@SIH Idea submission- Template",
        size=13, color=WHITE, align=PP_ALIGN.CENTER, font=F_ARIAL,
        anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, 1280, 768, 140, 38, str(page_num),
        size=14, color=WHITE, bold=True, align=PP_ALIGN.RIGHT, font=F_ARIAL,
        anchor=MSO_ANCHOR.MIDDLE)

def team_corner(slide):
    txt(slide, 34, 40, 180, 40, "VERITY", size=22, color=BLACK,
        italic=True, bold=False, font=F_TNR)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE PAGE  
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
white_bg(slide)

txt(slide, 0, 10, 1440, 80, "SMART INDIA HACKATHON 2026",
    size=52, color=NAVY, bold=True, align=PP_ALIGN.CENTER, font=F_GAR)
txt(slide, 34, 40, 240, 45, "VERITY", size=24, color=BLACK, italic=False, font=F_TNR)

main_x, main_w = 86, 1250
title_lines = [
    "PROBLEM STATEMENT ID - SIH26106",
    "",
    "PROBLEM STATEMENT TITLE - AI-POWERED EMAIL THREAT DETECTION,",
    "GEOLOCATION & FORENSIC INTELLIGENCE PLATFORM",
    "",
    "THEME - BLOCKCHAIN & CYBERSECURITY",
    "PS CATEGORY - SOFTWARE",
    "",
    "TEAM ID -",
    "TEAM NAME - VERITY",
]
y_cursor = 195
for ln in title_lines:
    if ln == "":
        y_cursor += 22
        continue
    bold = ln.startswith("PROBLEM")
    txt(slide, main_x, y_cursor, main_w, 42, ln, size=30, color=BLACK,
        bold=True, font=F_TNR)
    y_cursor += 52

txt(slide, 1030, 714, 330, 55, "TITLE PAGE", size=40, color=BLACK,
    bold=True, align=PP_ALIGN.RIGHT, font=F_TNR)

box(slide, 0, 767, 1440, 43, fill=NAVY, line=None)
txt(slide, 0, 768, 1440, 38, "@SIH Idea submission- Template",
    size=13, color=WHITE, align=PP_ALIGN.CENTER, font=F_ARIAL, anchor=MSO_ANCHOR.MIDDLE)
txt(slide, 1280, 768, 140, 38, "1", size=14, color=WHITE, bold=True,
    align=PP_ALIGN.RIGHT, font=F_ARIAL, anchor=MSO_ANCHOR.MIDDLE)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — CONCEPT (Solution overview)
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
white_bg(slide)
team_corner(slide)

txt(slide, 300, 10, 840, 70, "TRACEMAIL", size=48, color=BLACK,
    bold=True, align=PP_ALIGN.CENTER, font=F_TNR)
txt(slide, 120, 88, 1200, 42,
    "AI-Powered Email Threat Detection, Geolocation & Forensic Intelligence Platform",
    size=26, color=BLACK, bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

# ── Column 1: Incoming email ──
box(slide, 55, 200, 380, 360, fill=LBLUE, line=RGBColor(0x92,0x9A,0xB0), line_w=1.0)
txt(slide, 80, 218, 330, 34, "INCOMING EMAIL", size=17, color=BLACK, bold=True, font=F_TNR)
txt(slide, 80, 258, 330, 30, "From: CFO (Claimed)", size=13, color=BLACK, font=F_TNR)
txt(slide, 80, 296, 330, 60,
    "\u201CImmediate wire release\nrequired before close of bank\u201D",
    size=14, color=BLACK, italic=True, font=F_TNR)
line1 = [("Urgency Signal", 138), ("Financial Request", 166), ("Impersonation Claim", 194)]
for lbl, yy in line1:
    txt(slide, 80, 388 + (yy-138), 330, 24, lbl, size=13, color=BLACK, font=F_TNR)
txt(slide, 80, 540, 330, 30, "Potential Attack Vector", size=15, color=BLACK, bold=True, font=F_TNR)
txt(slide, 220, 540, 180, 30, "Detected", size=15, color=CRIMSON, bold=True, font=F_TNR)

# ── Column 2: Multi-signal forensic engine ──
box(slide, 475, 200, 380, 360, fill=LBLUE2, line=RGBColor(0x92,0x9A,0xB0), line_w=1.0)
txt(slide, 500, 210, 330, 30, "MULTI-SIGNAL FORENSIC ENGINE", size=16, color=BLACK, bold=True, font=F_TNR)
txt(slide, 505, 250, 330, 26, "SPF / DKIM / DMARC CHECK ONLY", size=14, color=BLACK, bold=True, font=F_TNR)
risks = [("IDENTITY RISK", 302), ("EVIDENCE RISK", 340), ("INFRA RISK", 378)]
for lbl, yy in risks:
    txt(slide, 520, yy, 200, 26, lbl, size=13, color=BLACK, bold=True, font=F_TNR)
    txt(slide, 700, yy, 120, 26, "HIGH", size=12, color=CRIMSON, bold=True, font=F_TNR,
        align=PP_ALIGN.RIGHT)
txt(slide, 500, 428, 330, 28, "MULTI-SIGNAL RISK ASSESSMENT", size=14, color=BLACK, bold=True, font=F_TNR)
for lbl, xx in [("LOW", 545), ("MEDIUM", 640), ("HIGH", 745)]:
    txt(slide, xx, 462, 80, 24, lbl, size=13, color=BLACK, bold=True, font=F_TNR,
        align=PP_ALIGN.CENTER)
for lbl, xx in [("ALLOW", 545), ("VERIFY", 622), ("BLOCK", 700)]:
    txt(slide, xx, 486, 90, 24, lbl, size=13, color=BLACK, bold=True, font=F_TNR,
        align=PP_ALIGN.CENTER)
txt(slide, 492, 515, 350, 30, "More Evidence => Higher Confidence", size=15,
    color=BLACK, bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

# ── Column 3: Independent verification ──
box(slide, 900, 200, 480, 360, fill=LBLUE, line=RGBColor(0x92,0x9A,0xB0), line_w=1.0)
txt(slide, 925, 218, 430, 30, "INDEPENDENT VERIFICATION", size=17, color=BLACK, bold=True, font=F_TNR)
txt(slide, 925, 270, 430, 30, "TraceMail Alert", size=15, color=BLACK, bold=True, font=F_TNR)
txt(slide, 925, 304, 430, 55,
    "An email claiming to be from your\nCFO requested :\n$25,000",
    size=14, color=BLACK, font=F_TNR)
txt(slide, 925, 390, 430, 24, "Verify this request ?", size=13, color=BLACK, font=F_TNR)
txt(slide, 925, 424, 300, 26, "Yes -  Confirmed", size=14, color=DGREEN, bold=True, font=F_TNR)
txt(slide, 925, 452, 300, 26, "No -  Quarantined", size=14, color=CRIMSON, bold=True, font=F_TNR)
txt(slide, 925, 520, 430, 28, "Fraud Prevented \u2014 suspicious email", size=14, color=BLACK,
    bold=True, font=F_TNR)
txt(slide, 925, 545, 430, 26, "quarantined before authorization", size=14, color=BLACK,
    bold=True, font=F_TNR)

# ── WHY TRACEMAIL ──
txt(slide, 300, 600, 840, 40, "WHY TRACEMAIL ??", size=21, color=BLACK, bold=True,
    align=PP_ALIGN.CENTER, font=F_TNR)
whys = [
    ("EMAIL \u2260 IDENTITY", "Don\u2019t trust the display name.\nVerify every contradiction.", 330),
    ("EVIDENCE-AWARE VERIFICATION", "More evidence -> Higher confidence.", 585),
    ("DETECT \u2192 PREVENT", "Detect the threat.\nStop the wire transfer.", 840),
]
for title, desc, xx in whys:
    txt(slide, xx, 648, 300, 40, title, size=16, color=BLACK, bold=True, align=PP_ALIGN.CENTER, font=F_TNR)
    txt(slide, xx, 690, 300, 50, desc, size=13, color=BLACK, align=PP_ALIGN.CENTER, font=F_TNR)

footer(slide, 2)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — TECHNICAL APPROACH
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
white_bg(slide)
team_corner(slide)

txt(slide, 0, 6, 1440, 64, "TECHNICAL APPROACH", size=48, color=BLACK,
    bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

# ── Left: System architecture ──
txt(slide, 200, 108, 700, 40, "TRACEMAIL SYSTEM", size=24, color=BLACK, bold=True, font=F_TNR)
txt(slide, 200, 148, 700, 40, "ARCHITECTURE", size=24, color=BLACK, bold=True, font=F_TNR)

arch = [
    ("RAW .EML", "Original evidence + SHA-256", "#ffc7ce", CRIMSON),
    ("1. EVIDENCE ACQUISITION", "MIME | headers | body | URLs", "#ffe699", RGBColor(0x9C,0x65,0x00)),
    ("2. EVIDENCE NORMALIZATION", "RFC-aware canonicalization", "#deebf7", BLUE),
    ("3. FORENSIC ENGINES", "identity | infra | campaign", "#e2efda", DGREEN),
    ("4. AI + INTELLIGENCE", "NLP | XGBoost | DNS/RDAP | GeoIP", "#deebf7", BLUE),
    ("5. CORRELATION", "Neo4j graph | campaign", "#e2efda", DGREEN),
    ("6. FORENSIC DECISION", "risk | confidence | evidence", "#ffe699", RGBColor(0x9C,0x65,0x00)),
    ("INVESTIGATION CASE", "graph | map | report", "#c6e0b4", DGREEN),
]
def parse_color(hexs):
    h = hexs.lstrip("#")
    return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

cols = [120, 470]
rows = [230, 340, 450, 560]
for i, (t, d, fill, lc) in enumerate(arch):
    c, r = i % 2, i // 2
    x, y = cols[c], rows[r]
    fillc = parse_color(fill)
    box(slide, x, y, 300, 88, fill=fillc, line=lc, line_w=1.2)
    txt(slide, x+12, y+8, 275, 30, t, size=14, color=BLACK, bold=True, font=F_TNR)
    txt(slide, x+12, y+42, 275, 34, d, size=11, color=GRAY, font=F_TNR)
    if c == 0:
        txt(slide, x+300, y+30, 20, 30, "\u25B6", size=16, color=BLACK, bold=True,
            font=F_ARIAL, align=PP_ALIGN.CENTER)
    else:
        txt(slide, x-30, y+30, 20, 30, "\u25B6", size=16, color=BLACK, bold=True,
            font=F_ARIAL, align=PP_ALIGN.LEFT)
for yy in [300, 410, 520]:
    txt(slide, 360, yy, 60, 26, "\u25BC", size=16, color=BLACK, font=F_ARIAL,
        align=PP_ALIGN.CENTER)

# ── Right: Technology stack ──
box(slide, 940, 80, 430, 650, fill=BLUE, line=None, r=0.03)
txt(slide, 940, 96, 430, 60, "TECHNOLOGY", size=24, color=WHITE, bold=True,
    align=PP_ALIGN.CENTER, font=F_TNR)
txt(slide, 940, 128, 430, 30, "STACK", size=24, color=WHITE, bold=True,
    align=PP_ALIGN.CENTER, font=F_TNR)

stack = [
    ("AI / NLP", ["PYTHON", "TRANSFORMER NLP", "XGBOOST", "SHAP"]),
    ("CORRELATION", ["NEO4J", "CYPHER", "GRAPH ANALYSIS"]),
    ("APPLICATION", ["REACT", "TYPESCRIPT", "FASTAPI", "LEAFLET / REACT FLOW"]),
    ("DATA", ["POSTGRESQL", "MINIO", "RDAP / DNS / GEOIP"]),
    ("SECURITY", ["HTTPS / TLS", "JWT / AUTHENTICATION", "SHA-256 HASHING", "CHAIN OF CUSTODY"]),
    ("DEPLOYMENT", ["DOCKER", "DOCKER COMPOSE", "CLOUD / SERVER"]),
]
yy = 175
for cat, items in stack:
    txt(slide, 965, yy, 380, 26, cat, size=14, color=WHITE, bold=True, font=F_TNR)
    yy += 30
    for it in items:
        txt(slide, 985, yy, 360, 24, "\u2022  " + it, size=12, color=WHITE, font=F_TNR)
        yy += 24
    yy += 8

footer(slide, 3)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — FEASIBILITY AND VIABILITY
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
white_bg(slide)
team_corner(slide)

txt(slide, 100, 16, 1240, 66, "FEASIBILITY AND VIABILITY", size=48, color=BLACK,
    bold=True, align=PP_ALIGN.CENTER, font=F_TNR)
txt(slide, 200, 92, 1040, 34,
    "A practical path from forensic prototype to real-world email investigation",
    size=24, color=GRAY, bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

# Column headers
colheads = [
    ("FEASIBLE NOW", 30, GREEN),
    ("KEY RISKS", 330, ORANGE),
    ("MITIGATION STRATEGY", 625, BLUE),
    ("VIABILITY & SCALE", 950, NAVY),
]
for label, xx, clr in colheads:
    txt(slide, xx, 180, 280, 30, label, size=18, color=clr, bold=True, font=F_TNR)

# Column 1 — Feasible now (light green box)
box(slide, 30, 225, 290, 345, fill=LBLUE2, line=GREEN, line_w=1.0)
feas = [
    "Open forensic datasets &\n.EML analysis tools",
    "Mature Python email/\nMIME parsers",
    "Pretrained Transformer\nNLP & XGBoost models",
    "FastAPI + React\necosystem",
    "Standard RFC-aware\nheader analysis",
    "Modular, cloud-ready\narchitecture",
]
yy = 240
for it in feas:
    txt(slide, 48, yy, 265, 52, it, size=15, color=GRAY, font=F_TNR)
    yy += 53

# Column 2 — Key risks
box(slide, 330, 225, 285, 345, fill=LBLUE2, line=ORANGE, line_w=1.0)
risks = [
    "False positives and\nfalse negatives",
    "Unseen social-engineering\ntechniques",
    "Missing / forged\nemail headers",
    "External API\nrate limits",
    "Evidence integrity\nchallenges",
    "Email privacy & consent\ncompliance",
]
yy = 240
for it in risks:
    txt(slide, 348, yy, 255, 52, it, size=15, color=GRAY, font=F_TNR)
    yy += 53

# Column 3 — Mitigation
box(slide, 625, 225, 285, 345, fill=LBLUE2, line=BLUE, line_w=1.0)
mit = [
    "Confidence thresholds:\nLow / Med / High",
    "Cross-dataset testing\nfor generalization",
    "Multi-signal validation &\nRFC-aware parsing",
    "Mock external APIs, real\nkeys for validation",
    "SHA-256 hashing +\ntamper-evident audit trail",
    "Encryption, consent &\nminimum data retention",
]
yy = 240
for it in mit:
    txt(slide, 643, yy, 258, 52, it, size=15, color=GRAY, font=F_TNR)
    yy += 53

# Column 4 — Viability & scale (navy box)
box(slide, 950, 225, 405, 345, fill=NAVY, line=None)
box(slide, 975, 255, 355, 34, fill=NAVY, line=None)
txt(slide, 975, 258, 355, 30, "FEASIBILITY ANALYSIS", size=17, color=WHITE, bold=True,
    font=F_TNR, align=PP_ALIGN.CENTER)
viab = [
    ("BUILDABLE:", "AI models, forensic parsers and graph databases are available today."),
    ("COST-VIABLE:", "Start with selective risk analysis and a controlled pilot (SOC)."),
    ("SCALABLE:", "API architecture supports enterprises, banks and government investigations."),
]
yy = 300
for key, val in viab:
    txt(slide, 973, yy, 120, 70, key, size=13, color=YELLOW, bold=True, font=F_TNR)
    txt(slide, 1085, yy, 245, 80, val, size=13, color=WHITE, font=F_TNR)
    yy += 76
txt(slide, 973, 520, 355, 26, "DEPLOYMENT ROADMAP", size=16, color=CYAN, bold=True,
    font=F_TNR, align=PP_ALIGN.CENTER)
txt(slide, 973, 550, 355, 26, "MVP \u2192 Pilot \u2192 Sector Integration \u2192 Scale",
    size=15, color=WHITE, bold=True, font=F_TNR, align=PP_ALIGN.CENTER)

# ── Bottom: fail-safe flow ──
txt(slide, 35, 618, 900, 30, "FAIL-SAFE FORENSIC INVESTIGATION FLOW",
    size=17, color=BLACK, bold=True, font=F_TNR)
flow = [
    ("HIGH-RISK EMAIL", 40),
    ("PRESERVATION", 255),
    ("IF TIMEOUT /\nUNAVAILABLE", 470),
    ("SECONDARY\nVERIFICATION", 690),
    ("DELAY OR\nQUARANTINE", 905),
    ("EVIDENCE\n& REPORT", 1115),
]
for lbl, xx in flow:
    box(slide, xx, 655, 195, 46, fill=LBLUE2, line=BLUE, line_w=1.0)
    txt(slide, xx + 4, 658, 187, 40, lbl, size=12, color=BLACK, bold=True,
        font=F_TNR, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
for ax in (236, 449, 668, 883, 1098):
    txt(slide, ax, 662, 36, 30, "\u25B6", size=18, color=BLACK, bold=True,
        font=F_ARIAL, align=PP_ALIGN.CENTER)
txt(slide, 300, 735, 840, 30,
    "\u201CHigh-risk emails are never silently dropped.\u201D",
    size=16, color=RED, bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

footer(slide, 4)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — IMPACT AND BENEFITS
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
white_bg(slide)
team_corner(slide)

txt(slide, 0, 6, 1440, 64, "IMPACT AND BENEFITS", size=48, color=BLACK,
    bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

# Left column
left_items = [
    ("PROTECTS PEOPLE", "Reduces impersonation risk"),
    ("PREVENTS FRAUD", "Stops loss before action"),
    ("REDUCES MANIPULATION", "Detects urgency and pressure"),
    ("BUILDS TRUST", "Safer email communication"),
]
for i, (t, d) in enumerate(left_items):
    yy = 160 + i * 95
    txt(slide, 130, yy, 360, 30, t, size=17, color=BLACK, bold=True, font=F_TNR)
    txt(slide, 130, yy + 28, 360, 26, d, size=15, color=GRAY, font=F_TNR)

# Right column
right_items = [
    ("MULTI-SIGNAL AI", "Identity + intent + context"),
    ("INDEPENDENT VERIFY", "Evidence-backed findings"),
    ("RISK-BASED ACTION", "Allow \u2022 Warn \u2022 Block"),
    ("AUDITABLE EVIDENCE", "Report-ready forensic logs"),
]
for i, (t, d) in enumerate(right_items):
    yy = 160 + i * 95
    txt(slide, 970, yy, 360, 30, t, size=17, color=BLACK, bold=True, font=F_TNR)
    txt(slide, 970, yy + 28, 360, 26, d, size=15, color=GRAY, font=F_TNR)

# Center — who we protect
txt(slide, 520, 195, 400, 40, "Who TraceMail Protects ?", size=27, color=BLACK,
    bold=True, align=PP_ALIGN.CENTER, font=F_TNR)
orbits = [
    ("CITIZENS", 560, 470, BLUE),
    ("FAMILIES", 620, 430, NAVY),
    ("ENTERPRISES", 690, 405, ORANGE),
    ("BANKS / TELECOM", 760, 375, RED),
]
for lbl, xx, yy, clr in orbits:
    circle(slide, xx-70, yy-24, 150, fill=clr)
    txt(slide, xx-70, yy-6, 150, 26, lbl, size=13, color=WHITE, bold=True,
        font=F_TNR, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# Bottom flow
flow5 = [
    ("Suspicious Email", 150, RED, 60),
    ("Forensic Analysis", 370, ORANGE, 140),
    ("Risk Assessment", 640, BLUE, 120),
    ("Independent Verification", 900, BLUE, 150),
    ("Prevented Fraud", 1180, NAVY, 120),
]
for lbl, xx, clr, wd in flow5:
    txt(slide, xx, 685, wd, 40, lbl, size=19, color=clr, bold=True,
        font=F_TNR, align=PP_ALIGN.CENTER)
for ax in (235, 470, 760, 1055):
    txt(slide, ax, 690, 34, 30, "\u25B6", size=22, color=BLACK, bold=True,
        font=F_ARIAL, align=PP_ALIGN.CENTER)

footer(slide, 5)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — RESEARCH AND REFERENCES
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
white_bg(slide)
team_corner(slide)

txt(slide, 150, 6, 1140, 64, "RESEARCH  AND REFERENCES", size=46, color=BLACK,
    bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

# Academic foundation
txt(slide, 200, 150, 500, 40, "ACADEMIC FOUNDATION", size=26, color=NAVY, bold=True, font=F_TNR)
acad = [
    "RFC 7489 \u2014 DMARC authentication policy",
    "RFC 7208 \u2014 SPF (Sender Policy Framework)",
    "RFC 6376 \u2014 DKIM email signing",
    "RFC 5322 \u2014 Email message format",
    "RFC 7482 / 7483 \u2014 RDAP registries",
]
yy = 205
for it in acad:
    txt(slide, 210, yy, 470, 30, it, size=17, color=GRAY, font=F_TNR)
    yy += 38

# Datasets & benchmarks
txt(slide, 780, 150, 500, 40, "DATASETS & BENCHMARKS", size=26, color=NAVY, bold=True, font=F_TNR)
dat = [
    "Public phishing & spam email corpora",
    "MIME / header parsing conformance suites",
    "Real-world BEC incident templates",
    "Used for training, fine-tuning and robustness testing",
]
yy = 205
for it in dat:
    txt(slide, 790, yy, 480, 30, it, size=17, color=GRAY, font=F_TNR)
    yy += 38

# Competitor landscape
txt(slide, 200, 420, 500, 40, "COMPETITOR LANDSCAPE", size=26, color=NAVY, bold=True, font=F_TNR)
comp = [
    ("MICROSOFT DEFENDER", "SPF/DKIM/DMARC, malware & phishing blocking"),
    ("PROOFPOINT", "Enterprise email security & gateway"),
    ("GOOGLE WORKSPACE", "Email protection & threat intelligence"),
    ("TRACEMAIL", "Evidence graph + identity contradiction + campaign discovery + attack-path reconstruction + confidence & provenance"),
]
yy = 475
for name, d in comp:
    txt(slide, 210, yy, 480, 30, name, size=16, color=BLACK, bold=True, font=F_TNR)
    txt(slide, 210, yy + 22, 480, 30, d, size=13, color=GRAY, font=F_TNR)
    yy += 58

# National cyber alignment
txt(slide, 780, 420, 500, 40, "NATIONAL CYBER ALIGNMENT", size=26, color=NAVY, bold=True, font=F_TNR)
nat = [
    ("Smart India Hackathon 2026", "Problem statement SIH26106 \u2014 Blockchain & Cybersecurity theme"),
    ("CERT-In", "India\u2019s national computer emergency response team"),
    ("cybercrime.gov.in", "National Cyber Crime Reporting Portal \u2014 victim reporting context"),
    ("1930 Cyber Fraud Helpline", "Fraud reporting and escalation reference"),
]
yy = 475
for name, d in nat:
    txt(slide, 790, yy, 480, 30, name, size=16, color=BLACK, bold=True, font=F_TNR)
    txt(slide, 790, yy + 22, 480, 30, d, size=13, color=GRAY, font=F_TNR)
    yy += 58

# Closing quote
txt(slide, 180, 700, 1080, 66,
    "\u201CDetection alone is insufficient for high-consequence actions.\n"
    "TraceMail adds forensic evidence & verification before authorization.\u201D",
    size=21, color=BLACK, bold=True, align=PP_ALIGN.CENTER, font=F_TNR)

footer(slide, 6)

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════════
out = r"C:\SIH\SIH_Hackathon_Presentation_6Slides.pptx"
prs.save(out)
print(f"Saved: {out}")
print(f"Slides: {len(prs.slides)}")