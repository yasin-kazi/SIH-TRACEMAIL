#!/usr/bin/env python3
"""
SIH26106 Hackathon Presentation Generator
Creates a professional, competition-ready PPTX.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# ─── Color Palette (from DESIGN.md) ───────────────────────────────────────────
BG_DARK       = RGBColor(0x0A, 0x0D, 0x14)   # Base Void
SURFACE_01    = RGBColor(0x10, 0x16, 0x22)   # Panel
SURFACE_02    = RGBColor(0x18, 0x22, 0x34)   # Raised
STROKE_M      = RGBColor(0x23, 0x32, 0x4A)   # Stroke Muted
CYAN          = RGBColor(0x06, 0xB6, 0xD4)   # Tactical Cyan (Primary)
COBALT        = RGBColor(0x3B, 0x82, 0xF6)   # Electric Cobalt
EMERALD       = RGBColor(0x10, 0xB9, 0x81)   # Verified Emerald
CRIMSON       = RGBColor(0xEF, 0x44, 0x44)   # Critical Threat Crimson
AMBER         = RGBColor(0xF5, 0x9E, 0x0B)   # Suspicious Amber
TEXT_HIGH     = RGBColor(0xF1, 0xF5, 0xF9)   # High-contrast text
TEXT_SUPPORT  = RGBColor(0x94, 0xA3, 0xB8)   # Supporting text
TEXT_MUTED    = RGBColor(0x47, 0x55, 0x69)   # Muted text
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
NEAR_BLACK    = RGBColor(0x08, 0x0E, 0x1A)

# ─── Presentation Setup ────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
W = prs.slide_width
H = prs.slide_height

# ─── Helper Functions ──────────────────────────────────────────────────────────
def dark_bg(slide):
    """Fill slide background with dark color."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_DARK

def add_rect(slide, left, top, width, height, fill_color=None, border_color=None, border_width=Pt(1)):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    ln = shape.line
    if border_color:
        ln.color.rgb = border_color
        ln.width = border_width
    else:
        ln.fill.background()
    shape.adjustments[0] = 0.04  # corner radius
    return shape

def add_text_box(slide, left, top, width, height, text, font_size=14, color=TEXT_HIGH,
                 bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri", anchor=MSO_ANCHOR.TOP,
                 line_spacing=1.15):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    txBox.text_frame.word_wrap = True
    txBox.text_frame.auto_size = None
    p = txBox.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    run = p.runs[0] if p.runs else None
    if run:
        run.font.name = font_name
    txBox.text_frame.paragraphs[0].line_spacing = Pt(int(font_size * line_spacing))
    return txBox

def add_multiline(slide, left, top, width, height, lines, font_size=13, color=TEXT_HIGH,
                  bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri", spacing=1.3,
                  bullet=False, bullet_char="\u25B8"):
    """lines: list of (text, color, bold, font_size) tuples or just strings."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    for i, line_data in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        if isinstance(line_data, str):
            p.text = line_data
            p.font.size = Pt(font_size)
            p.font.color.rgb = color
            p.font.bold = bold
        elif isinstance(line_data, tuple):
            txt = line_data[0]
            if bullet:
                txt = f"{bullet_char} {txt}"
            p.text = txt
            p.font.size = Pt(line_data[1] if len(line_data) > 1 and isinstance(line_data[1], (int, float)) else font_size)
            p.font.color.rgb = line_data[2] if len(line_data) > 2 and isinstance(line_data[2], RGBColor) else color
            p.font.bold = line_data[3] if len(line_data) > 3 and isinstance(line_data[3], bool) else bold
        p.font.name = font_name
        p.alignment = alignment
        p.space_before = Pt(2)
        p.space_after = Pt(2)
        p.line_spacing = Pt(int((p.font.size or Pt(font_size)).pt * spacing))
    return txBox

def add_accent_line(slide, left, top, width, color=CYAN):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Pt(3))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape

def add_section_header(slide, text, subtitle="", left=Inches(0.8), top=Inches(0.5)):
    add_text_box(slide, left, top, Inches(11.5), Inches(0.6), text,
                 font_size=32, color=TEXT_HIGH, bold=True, font_name="Calibri")
    add_accent_line(slide, left, top + Inches(0.65), Inches(2.5), CYAN)
    if subtitle:
        add_text_box(slide, left, top + Inches(0.85), Inches(11.5), Inches(0.5), subtitle,
                     font_size=16, color=TEXT_SUPPORT, font_name="Calibri")

def add_slide_number(slide, num, total):
    add_text_box(slide, Inches(12.2), Inches(7.0), Inches(1.0), Inches(0.4),
                 f"{num}/{total}", font_size=10, color=TEXT_MUTED, alignment=PP_ALIGN.RIGHT)

def add_footer_bar(slide):
    add_rect(slide, Inches(0), Inches(7.15), W, Inches(0.35), fill_color=SURFACE_01, border_color=STROKE_M, border_width=Pt(0.5))
    add_text_box(slide, Inches(0.5), Inches(7.17), Inches(4), Inches(0.3),
                 "SIH26106  |  Forensic Email Intelligence Platform", font_size=8, color=TEXT_MUTED)

TOTAL_SLIDES = 19

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
dark_bg(slide)

# Top accent bar
add_rect(slide, Inches(0), Inches(0), W, Inches(0.06), fill_color=CYAN)

# Center content area
add_rect(slide, Inches(1.5), Inches(1.8), Inches(10.3), Inches(4.2), fill_color=SURFACE_01, border_color=STROKE_M)

# SIH badge
add_rect(slide, Inches(5.0), Inches(2.1), Inches(3.3), Inches(0.55), fill_color=SURFACE_02, border_color=CYAN)
add_text_box(slide, Inches(5.0), Inches(2.15), Inches(3.3), Inches(0.5),
             "SMART INDIA HACKATHON 2026", font_size=12, color=CYAN, bold=True, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Problem ID
add_text_box(slide, Inches(1.5), Inches(2.9), Inches(10.3), Inches(0.5),
             "SIH26106", font_size=18, color=TEXT_SUPPORT, alignment=PP_ALIGN.CENTER, font_name="Consolas")

# Main title
add_text_box(slide, Inches(1.8), Inches(3.4), Inches(9.7), Inches(1.2),
             "AI-Powered Email Forensic\nIntelligence Platform", font_size=40, color=TEXT_HIGH, bold=True,
             alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Accent line under title
add_accent_line(slide, Inches(4.5), Inches(4.65), Inches(4.3), CYAN)

# Subtitle
add_text_box(slide, Inches(1.8), Inches(4.85), Inches(9.7), Inches(0.7),
             "Evidence-Driven Email Threat Detection, Geolocation &\nForensic Intelligence for Investigative Cybersecurity",
             font_size=16, color=TEXT_SUPPORT, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Bottom tags
add_rect(slide, Inches(3.0), Inches(5.65), Inches(7.3), Inches(0.35), fill_color=SURFACE_02, border_color=STROKE_M, border_width=Pt(0.5))
add_text_box(slide, Inches(3.0), Inches(5.67), Inches(7.3), Inches(0.3),
             "BLOCKCHAIN & CYBERSECURITY  |  EMAIL FORENSICS  |  AI/ML  |  INVESTIGATIVE INTELLIGENCE",
             font_size=9, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER, font_name="Consolas")

# Bottom accent bar
add_rect(slide, Inches(0), Inches(7.15), W, Inches(0.35), fill_color=SURFACE_01)
add_text_box(slide, Inches(0.5), Inches(7.17), Inches(5), Inches(0.3),
             "TraceMail  |  Forensic Email Evidence Engine", font_size=9, color=TEXT_MUTED)

add_slide_number(slide, 1, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — PROBLEM STATEMENT
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Problem Statement", "Why this problem matters")
add_footer_bar(slide)

# Stats boxes row
stats = [
    ("$2.4B+", "BEC losses reported\nto FBI IC3 in 2023", CRIMSON),
    ("36%", "of data breaches involve\nphishing attacks", AMBER),
    ("91%", "of cyberattacks begin\nwith a phishing email", CRIMSON),
    ("75%", "of organizations faced\nemail fraud in 2024", AMBER),
]
for i, (val, desc, accent) in enumerate(stats):
    x = Inches(0.8 + i * 3.05)
    y = Inches(1.8)
    add_rect(slide, x, y, Inches(2.8), Inches(1.6), fill_color=SURFACE_01, border_color=accent, border_width=Pt(1.5))
    add_text_box(slide, x, y + Inches(0.2), Inches(2.8), Inches(0.6), val,
                 font_size=34, color=accent, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
    add_text_box(slide, x, y + Inches(0.85), Inches(2.8), Inches(0.6), desc,
                 font_size=11, color=TEXT_SUPPORT, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Problem description
add_rect(slide, Inches(0.8), Inches(3.7), Inches(11.7), Inches(3.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(1.1), Inches(3.85), Inches(11.1), Inches(0.4),
             "THE CORE PROBLEM", font_size=11, color=CYAN, bold=True, font_name="Consolas")

problem_lines = [
    ("Email remains the #1 attack vector for cybercrime, BEC fraud, and targeted phishing campaigns.", 14, TEXT_HIGH),
    ("", 6, TEXT_HIGH),
    ("Current email security tools focus on automated filtering and blocking. They fail to provide:", 14, TEXT_SUPPORT),
    ("", 4, TEXT_HIGH),
    ("Forensic-grade evidence analysis that investigators can use in legal proceedings", 13, TEXT_HIGH, False),
    ("Cross-case correlation to discover coordinated attack campaigns", 13, TEXT_HIGH, False),
    ("Explainable reasoning — showing WHY an email is suspicious, not just a binary verdict", 13, TEXT_HIGH, False),
    ("Identity contradiction detection across email headers, authentication, and infrastructure", 13, TEXT_HIGH, False),
    ("Attack path reconstruction with evidence provenance and confidence scores", 13, TEXT_HIGH, False),
]
add_multiline(slide, Inches(1.1), Inches(4.25), Inches(11.1), Inches(2.4),
              [(l[0], l[1], l[2] if len(l) > 2 else TEXT_HIGH, False) for l in problem_lines],
              bullet=False, spacing=1.4)

add_slide_number(slide, 2, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — PROBLEM CONTEXT / EXISTING CHALLENGES
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Problem Context", "Existing challenges in email forensics")
add_footer_bar(slide)

# Left column — Challenges
add_rect(slide, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(1.0), Inches(1.85), Inches(5.3), Inches(0.35),
             "CURRENT LIMITATIONS", font_size=10, color=CRIMSON, bold=True, font_name="Consolas")

challenges = [
    ("SPF/DKIM/DMARC Alone Are Insufficient", "Authentication passing does NOT establish legitimate intent. Compromised accounts still pass all checks."),
    ("No Identity Contradiction Detection", "From vs Reply-To vs Return-Path mismatches go undetected by standard filters."),
    ("No Cross-Case Correlation", "Related attacks using the same infrastructure are treated as isolated incidents."),
    ("Black-Box Classification", "Analysts receive a threat verdict but cannot see which evidence contributed to it."),
    ("No Forensic Evidence Provenance", "Findings lack chain-of-custody tracking needed for legal proceedings."),
    ("No Attack Path Reconstruction", "Investigations stop at individual emails without mapping the full attack infrastructure."),
]
for i, (title, desc) in enumerate(challenges):
    yy = Inches(2.35 + i * 0.78)
    add_rect(slide, Inches(1.0), yy, Inches(5.3), Inches(0.7), fill_color=SURFACE_02, border_color=STROKE_M, border_width=Pt(0.5))
    add_text_box(slide, Inches(1.15), yy + Inches(0.05), Inches(5.0), Inches(0.3),
                 title, font_size=12, color=AMBER, bold=True, font_name="Calibri")
    add_text_box(slide, Inches(1.15), yy + Inches(0.35), Inches(5.0), Inches(0.3),
                 desc, font_size=10, color=TEXT_SUPPORT, font_name="Calibri")

# Right column — Commercial gap
add_rect(slide, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(7.0), Inches(1.85), Inches(5.3), Inches(0.35),
             "COMMERCIAL PRODUCTS", font_size=10, color=COBALT, bold=True, font_name="Consolas")

add_text_box(slide, Inches(7.0), Inches(2.35), Inches(5.3), Inches(0.5),
             "Microsoft Defender, Proofpoint, and Google Workspace provide sophisticated\nemail security — but as BLOCKING tools, not INVESTIGATION platforms.",
             font_size=12, color=TEXT_SUPPORT, font_name="Calibri")

gap_items = [
    "Single-email classification, not campaign discovery",
    "Binary threat verdicts, not evidence-weighted reasoning",
    "No identity contradiction mapping across headers",
    "No forensic report generation with chain-of-custody",
    "No interactive investigation graph or attack path",
    "No explainable multi-evidence decision engine",
]
add_text_box(slide, Inches(7.0), Inches(3.1), Inches(5.3), Inches(0.3),
             "KEY GAPS IN EXISTING SOLUTIONS:", font_size=10, color=CYAN, bold=True, font_name="Consolas")

for i, item in enumerate(gap_items):
    add_text_box(slide, Inches(7.0), Inches(3.55 + i * 0.4), Inches(5.2), Inches(0.35),
                 f"\u25B8  {item}", font_size=11, color=TEXT_HIGH, font_name="Calibri")

add_rect(slide, Inches(7.0), Inches(6.0), Inches(5.3), Inches(0.55), fill_color=SURFACE_02, border_color=EMERALD, border_width=Pt(1))
add_text_box(slide, Inches(7.0), Inches(6.05), Inches(5.3), Inches(0.45),
             "THE GAP: No platform combines forensic reasoning,\ncampaign discovery, and explainable multi-evidence decisions.",
             font_size=11, color=EMERALD, bold=True, font_name="Calibri")

add_slide_number(slide, 3, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — PROPOSED SOLUTION
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Proposed Solution", "Forensic Email Evidence Engine")
add_footer_bar(slide)

# Central concept box
add_rect(slide, Inches(0.8), Inches(1.7), Inches(11.7), Inches(1.3), fill_color=SURFACE_01, border_color=CYAN, border_width=Pt(1.5))
add_text_box(slide, Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.4),
             "CONCEPT", font_size=10, color=CYAN, bold=True, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(2.15), Inches(11.3), Inches(0.7),
             "Treat every email as a forensic evidence package rather than simply a classification input. "
             "Convert suspicious emails into structured forensic evidence graphs, detect contradictions across "
             "sender identity and infrastructure, correlate evidence across multiple incidents to discover campaigns, "
             "and show confidence and provenance for every investigative finding.",
             font_size=13, color=TEXT_HIGH, font_name="Calibri")

# Pipeline steps
pipeline_steps = [
    ("RAW\n.EML", "Ingestion"),
    ("Evidence\nExtraction", "MIME parsing\nSHA-256 hash"),
    ("Evidence\nNormalization", "RFC-aware\nCanonicalize"),
    ("Forensic\nEngines", "Identity\nInfrastructure"),
    ("AI +\nIntelligence", "NLP / ML\nThreat Intel"),
    ("Correlation", "Graph +\nCampaign"),
    ("Forensic\nDecision", "Risk +\nConfidence"),
    ("Investigation\nCase", "Report\nGraph"),
]

for i, (step, detail) in enumerate(pipeline_steps):
    x = Inches(0.65 + i * 1.55)
    y = Inches(3.35)
    add_rect(slide, x, y, Inches(1.35), Inches(1.5), fill_color=SURFACE_02, border_color=CYAN, border_width=Pt(1))
    add_text_box(slide, x, y + Inches(0.15), Inches(1.35), Inches(0.7),
                 step, font_size=11, color=TEXT_HIGH, bold=True, alignment=PP_ALIGN.CENTER, font_name="Calibri")
    add_text_box(slide, x, y + Inches(0.85), Inches(1.35), Inches(0.5),
                 detail, font_size=8, color=TEXT_SUPPORT, alignment=PP_ALIGN.CENTER, font_name="Calibri")
    if i < len(pipeline_steps) - 1:
        add_text_box(slide, x + Inches(1.35), y + Inches(0.55), Inches(0.2), Inches(0.3),
                     "\u25B6", font_size=12, color=CYAN, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Key questions answered
add_rect(slide, Inches(0.8), Inches(5.15), Inches(5.6), Inches(1.8), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(1.0), Inches(5.25), Inches(5.2), Inches(0.3),
             "INVESTIGATIVE QUESTIONS ANSWERED", font_size=10, color=EMERALD, bold=True, font_name="Consolas")
questions = [
    "What happened? Why is this email suspicious?",
    "Which evidence supports that conclusion?",
    "Which evidence contradicts it?",
    "How reliable is each finding?",
    "What infrastructure is associated with the email?",
    "Are other emails connected to the same campaign?",
    "What can and cannot be concluded from available evidence?",
]
for i, q in enumerate(questions):
    add_text_box(slide, Inches(1.0), Inches(5.6 + i * 0.2), Inches(5.2), Inches(0.2),
                 f"\u2713  {q}", font_size=9, color=TEXT_HIGH, font_name="Calibri")

# Differentiator callout
add_rect(slide, Inches(6.7), Inches(5.15), Inches(5.8), Inches(1.8), fill_color=SURFACE_02, border_color=EMERALD, border_width=Pt(1.5))
add_text_box(slide, Inches(6.9), Inches(5.25), Inches(5.4), Inches(0.3),
             "NOT A GENERIC PROJECT", font_size=10, color=EMERALD, bold=True, font_name="Consolas")
add_text_box(slide, Inches(6.9), Inches(5.6), Inches(5.4), Inches(1.2),
             "This is NOT another \"React + FastAPI + ML + Neo4j + dashboard\" project.\n\n"
             "The differentiation is in the FORENSIC REASONING ENGINE — how evidence is "
             "represented, how contradictions are detected, how reliability is calculated, "
             "and how uncertainty is communicated to analysts.",
             font_size=11, color=TEXT_HIGH, font_name="Calibri")

add_slide_number(slide, 4, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — TARGET USERS / STAKEHOLDERS
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Target Users & Stakeholders", "Who benefits from this platform")
add_footer_bar(slide)

users = [
    ("SOC Analysts", "Security Operations Center analysts who investigate suspicious emails, triage alerts, and need forensic-grade analysis with explainable findings.", CYAN, "\uD83D\uDD0D"),
    ("Incident Responders", "Teams responding to active breaches who need rapid campaign discovery, infrastructure mapping, and attack path reconstruction.", CRIMSON, "\u26A1"),
    ("Forensic Investigators", "Digital forensics professionals who need chain-of-custody evidence preservation, forensic reports, and legally defensible analysis.", EMERALD, "\uD83D\uDD0F"),
    ("Threat Intelligence Teams", "Teams building threat intelligence who need cross-case correlation, campaign clustering, and infrastructure fingerprinting.", COBALT, "\uD83D\uDCCA"),
    ("CISOs & Security Leadership", "Leadership who need risk dashboards, campaign visibility, and compliance-ready forensic reporting for executive briefings.", AMBER, "\uD83D\uDCCB"),
    ("Law Enforcement", "Agencies investigating cybercrime who need forensically sound evidence packages with chain-of-custody documentation for prosecution.", CRIMSON, "\u2696\uFE0F"),
]

for i, (title, desc, color, icon) in enumerate(users):
    col = i % 3
    row = i // 3
    x = Inches(0.8 + col * 4.1)
    y = Inches(1.7 + row * 2.75)
    add_rect(slide, x, y, Inches(3.8), Inches(2.4), fill_color=SURFACE_01, border_color=color, border_width=Pt(1.5))
    add_text_box(slide, x + Inches(0.2), y + Inches(0.2), Inches(3.4), Inches(0.4),
                 title, font_size=18, color=color, bold=True, font_name="Calibri")
    add_text_box(slide, x + Inches(0.2), y + Inches(0.75), Inches(3.4), Inches(1.5),
                 desc, font_size=11, color=TEXT_SUPPORT, font_name="Calibri")
    # Color accent bar at bottom
    add_rect(slide, x, y + Inches(2.15), Inches(3.8), Inches(0.25), fill_color=color)

add_slide_number(slide, 5, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — KEY FEATURES
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Key Features", "Six forensic engines powering the platform")
add_footer_bar(slide)

engines = [
    ("Identity Contradiction\nEngine", "Compares Display Name, From, Reply-To, Return-Path, DKIM domain, DMARC alignment, and sending infrastructure. Calculates Identity Consistency Score (0-100). Detects executive impersonation, lookalike domains, and header spoofing.", CRIMSON),
    ("Infrastructure\nFingerprinting Engine", "Builds IP -> ASN -> ISP -> Hosting -> DNS -> Domain -> MX profiles. Identifies cloud hosting, VPN, TOR, proxy, open relay, and suspicious hosting indicators. Maps probable source infrastructure.", AMBER),
    ("Campaign Discovery\nEngine", "Correlates emails across shared domains, IPs, URLs, language patterns, sender identities, timing, and hosting. Discovers campaigns from multi-email evidence graphs.", COBALT),
    ("Evidence Reliability\nEngine", "Every finding has: Evidence, Source, Type, Reliability, Confidence, Timestamp, Supporting relationships, Contradicting evidence. Distinguishes HIGH/MEDIUM/LOWER confidence.", EMERALD),
    ("Attack Path\nReconstruction", "Reconstructs: Sender identity -> Email infrastructure -> Received hops -> Sending IP -> Domain -> URL -> Hosting/ASN -> Related infrastructure -> Related cases. Shows observed vs inferred vs uncertain.", CYAN),
    ("Multi-Evidence\nDecision Engine", "Combines technical, identity, linguistic, infrastructure, historical, and relationship evidence. Outputs: Threat Class + Risk + Confidence + Evidence Contributions + Investigation Hypothesis.", TEXT_HIGH),
]

for i, (title, desc, color) in enumerate(engines):
    col = i % 3
    row = i // 3
    x = Inches(0.8 + col * 4.1)
    y = Inches(1.7 + row * 2.75)
    add_rect(slide, x, y, Inches(3.8), Inches(2.4), fill_color=SURFACE_01, border_color=color, border_width=Pt(1))
    # Engine number badge
    add_rect(slide, x + Inches(0.15), y + Inches(0.15), Inches(0.35), Inches(0.35), fill_color=color)
    add_text_box(slide, x + Inches(0.15), y + Inches(0.17), Inches(0.35), Inches(0.3),
                 str(i + 1), font_size=14, color=BG_DARK, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
    add_text_box(slide, x + Inches(0.6), y + Inches(0.15), Inches(3.0), Inches(0.6),
                 title, font_size=14, color=color, bold=True, font_name="Calibri")
    add_text_box(slide, x + Inches(0.2), y + Inches(0.8), Inches(3.4), Inches(1.5),
                 desc, font_size=10, color=TEXT_SUPPORT, font_name="Calibri")

add_slide_number(slide, 6, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — USER JOURNEY / WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "User Journey / Workflow", "From suspicious email to forensic investigation case")
add_footer_bar(slide)

# Main flow — 3 phases
phases = [
    ("PHASE 1: INGESTION & PRESERVATION", CYAN, [
        "1. Upload suspicious .EML file",
        "2. Calculate SHA-256 integrity hash",
        "3. Parse MIME structure & headers",
        "4. Reconstruct Received chain",
        "5. Store in encrypted evidence vault",
    ]),
    ("PHASE 2: ANALYSIS & INTELLIGENCE", AMBER, [
        "6. Analyze SPF / DKIM / DMARC",
        "7. Compare From / Reply-To / Return-Path",
        "8. Detect lookalike domains",
        "9. Extract & analyze URLs",
        "10. IP / ASN / Hosting analysis",
        "11. Run NLP / BEC analysis",
        "12. Query threat intelligence APIs",
    ]),
    ("PHASE 3: CORRELATION & DECISION", EMERALD, [
        "13. Build evidence graph",
        "14. Search previous cases",
        "15. Discover related emails",
        "16. Create campaign relationship",
        "17. Calculate risk & confidence",
        "18. Reconstruct attack path",
        "19. Generate forensic report",
    ]),
]

for i, (phase_title, color, steps) in enumerate(phases):
    x = Inches(0.8 + i * 4.1)
    y = Inches(1.7)
    # Phase header
    add_rect(slide, x, y, Inches(3.8), Inches(0.5), fill_color=color)
    add_text_box(slide, x + Inches(0.15), y + Inches(0.08), Inches(3.5), Inches(0.35),
                 phase_title, font_size=10, color=BG_DARK, bold=True, font_name="Consolas")
    # Steps
    add_rect(slide, x, y + Inches(0.5), Inches(3.8), Inches(4.2), fill_color=SURFACE_01, border_color=color, border_width=Pt(1))
    for j, step in enumerate(steps):
        add_text_box(slide, x + Inches(0.2), y + Inches(0.7 + j * 0.45), Inches(3.4), Inches(0.4),
                     step, font_size=12, color=TEXT_HIGH, font_name="Calibri")

# Arrows between phases
for i in range(2):
    x = Inches(4.6 + i * 4.1)
    add_text_box(slide, x, Inches(3.5), Inches(0.4), Inches(0.4),
                 "\u25B6", font_size=20, color=CYAN, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Bottom — Analyst output
add_rect(slide, Inches(0.8), Inches(6.4), Inches(11.7), Inches(0.6), fill_color=SURFACE_02, border_color=EMERALD, border_width=Pt(1))
add_text_box(slide, Inches(1.0), Inches(6.45), Inches(11.3), Inches(0.5),
             "ANALYST OUTPUT  \u2502  Forensic Report with: Case ID, Evidence Hash, Header Analysis, Authentication Status, "
             "Identity Consistency, Infrastructure Findings, Threat Classification, Risk Score, Evidence Confidence, "
             "Related Entities, Campaign Relationships, Attack Path Timeline, Attribution Limitations, Chain of Custody",
             font_size=10, color=TEXT_HIGH, font_name="Calibri")

add_slide_number(slide, 7, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — UI/UX OVERVIEW: INVESTIGATION OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "UI/UX Overview", "Investigation Overview — Case #1042")
add_footer_bar(slide)

# Left side — UI screenshot placeholder with description
add_rect(slide, Inches(0.8), Inches(1.7), Inches(5.5), Inches(5.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(1.0), Inches(1.85), Inches(5.1), Inches(0.3),
             "INVESTIGATION OVERVIEW SCREEN", font_size=10, color=CYAN, bold=True, font_name="Consolas")

# Simulated UI elements
# Threat gauge
add_rect(slide, Inches(1.0), Inches(2.35), Inches(2.5), Inches(2.0), fill_color=SURFACE_02, border_color=CRIMSON, border_width=Pt(1.5))
add_text_box(slide, Inches(1.0), Inches(2.45), Inches(2.5), Inches(0.3),
             "THREAT INDEX", font_size=9, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(2.8), Inches(2.5), Inches(0.8),
             "91", font_size=52, color=CRIMSON, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(3.6), Inches(2.5), Inches(0.4),
             "CRITICAL SEVERITY", font_size=10, color=CRIMSON, alignment=PP_ALIGN.CENTER, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(3.9), Inches(2.5), Inches(0.3),
             "BEC HIGH  |  REF #1042", font_size=8, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER, font_name="Consolas")

# Confidence bars
add_rect(slide, Inches(3.7), Inches(2.35), Inches(2.4), Inches(2.0), fill_color=SURFACE_02, border_color=STROKE_M)
add_text_box(slide, Inches(3.85), Inches(2.45), Inches(2.1), Inches(0.3),
             "CONFIDENCE", font_size=9, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER, font_name="Consolas")
add_text_box(slide, Inches(3.85), Inches(2.85), Inches(2.1), Inches(0.25),
             "Model Confidence", font_size=9, color=TEXT_SUPPORT, font_name="Calibri")
add_rect(slide, Inches(3.85), Inches(3.1), Inches(2.1), Inches(0.15), fill_color=SURFACE_01)
add_rect(slide, Inches(3.85), Inches(3.1), Inches(1.87), Inches(0.15), fill_color=CYAN)
add_text_box(slide, Inches(3.85), Inches(3.3), Inches(2.1), Inches(0.2),
             "89.4%", font_size=10, color=CYAN, bold=True, alignment=PP_ALIGN.RIGHT, font_name="Consolas")
add_text_box(slide, Inches(3.85), Inches(3.6), Inches(2.1), Inches(0.25),
             "Evidence Confidence", font_size=9, color=TEXT_SUPPORT, font_name="Calibri")
add_rect(slide, Inches(3.85), Inches(3.85), Inches(2.1), Inches(0.15), fill_color=SURFACE_01)
add_rect(slide, Inches(3.85), Inches(3.85), Inches(1.82), Inches(0.15), fill_color=EMERALD)
add_text_box(slide, Inches(3.85), Inches(4.05), Inches(2.1), Inches(0.2),
             "87.1%", font_size=10, color=EMERALD, bold=True, alignment=PP_ALIGN.RIGHT, font_name="Consolas")

# Metric tiles
metrics = [
    ("IDENTITY SYNC", "34/100", "High Contradiction", CRIMSON),
    ("RELATED EMAILS", "03", "Cluster #17", COBALT),
    ("INFRA NODES", "04", "2 DC + 1 Lookalike", CYAN),
    ("VAULT ARCHIVE", "EV-1042-01", "Merkle Tree Linked", EMERALD),
]
for i, (label, val, detail, color) in enumerate(metrics):
    col = i % 2
    row = i // 2
    x = Inches(1.0 + col * 2.6)
    y = Inches(4.6 + row * 0.9)
    add_rect(slide, x, y, Inches(2.35), Inches(0.8), fill_color=SURFACE_02, border_color=STROKE_M, border_width=Pt(0.5))
    add_text_box(slide, x + Inches(0.1), y + Inches(0.05), Inches(2.15), Inches(0.2),
                 label, font_size=7, color=TEXT_MUTED, font_name="Consolas")
    add_text_box(slide, x + Inches(0.1), y + Inches(0.25), Inches(2.15), Inches(0.25),
                 val, font_size=16, color=color, bold=True, font_name="Consolas")
    add_text_box(slide, x + Inches(0.1), y + Inches(0.55), Inches(2.15), Inches(0.2),
                 detail, font_size=8, color=TEXT_SUPPORT, font_name="Calibri")

# Right side — feature callouts
add_rect(slide, Inches(6.6), Inches(1.7), Inches(5.9), Inches(5.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(6.8), Inches(1.85), Inches(5.5), Inches(0.3),
             "SCREEN COMPONENTS", font_size=10, color=CYAN, bold=True, font_name="Consolas")

ui_features = [
    ("Live Evidence Feed", "Real-time triage stream with tactical packet inspection on MX clusters. FREEZE button pauses for audit.", CYAN),
    ("Threat Matrix Card", "Circular radial SVG gauge with 91/100 threat index. Model & Evidence confidence bars with non-repudiation status.", CRIMSON),
    ("Flagged Anomalies", "Weighted anomaly signals: Reply-To mismatch (+35), Lookalike domain (+28), C-Suite impersonation (+22), Bulletproof VPS (+18), BEC urgency (+24).", AMBER),
    ("Identity Routing Vector", "Visual comparison of Envelope From vs Reply-To vs Return-Path with SPOOFED / REDIRECT / MX-DROP status badges.", EMERALD),
    ("Attack Path Pipeline", "5-step visual flow: Identity Forgery -> .eml Ingestion -> TOR Exit IP -> Lookalike Domain -> Fast-Flux MX C2 Gate.", COBALT),
    ("Investigative Drilldowns", "4 action buttons: Examine Identity (contradiction map), View Attack Graph (C2 topology), Campaign Correlation (3 matches), Export Audit (PDF).", TEXT_HIGH),
]

for i, (title, desc, color) in enumerate(ui_features):
    yy = Inches(2.3 + i * 0.78)
    add_rect(slide, Inches(6.8), yy, Inches(5.5), Inches(0.7), fill_color=SURFACE_02, border_color=STROKE_M, border_width=Pt(0.5))
    add_text_box(slide, Inches(6.95), yy + Inches(0.05), Inches(5.2), Inches(0.25),
                 title, font_size=11, color=color, bold=True, font_name="Calibri")
    add_text_box(slide, Inches(6.95), yy + Inches(0.3), Inches(5.2), Inches(0.35),
                 desc, font_size=9, color=TEXT_SUPPORT, font_name="Calibri")

add_slide_number(slide, 8, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — UI/UX OVERVIEW: IDENTITY CONTRADICTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "UI/UX: Identity Contradiction Engine", "Signature component — detecting sender identity fraud")
add_footer_bar(slide)

# Left — Identity Consistency Score
add_rect(slide, Inches(0.8), Inches(1.7), Inches(3.8), Inches(5.1), fill_color=SURFACE_01, border_color=CRIMSON, border_width=Pt(1.5))
add_text_box(slide, Inches(1.0), Inches(1.85), Inches(3.4), Inches(0.3),
             "IDENTITY CONSISTENCY", font_size=10, color=CYAN, bold=True, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(2.25), Inches(1.5), Inches(0.7),
             "34", font_size=52, color=CRIMSON, bold=True, font_name="Consolas")
add_text_box(slide, Inches(2.2), Inches(2.55), Inches(1.5), Inches(0.4),
             "/ 100", font_size=20, color=TEXT_MUTED, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(3.0), Inches(3.4), Inches(0.3),
             "4 Severe Contradictions Detected", font_size=11, color=TEXT_SUPPORT, font_name="Calibri")
add_rect(slide, Inches(1.0), Inches(3.4), Inches(3.4), Inches(0.15), fill_color=SURFACE_02)
add_rect(slide, Inches(1.0), Inches(3.4), Inches(1.16), Inches(0.15), fill_color=CRIMSON)

# Discrepancy tree
discrepancies = [
    ("CLAIMED IDENTITY", "Robert Sterling (CFO)", "Executive Spoof", CRIMSON),
    ("RFC 5322 FROM", "r.sterling@acme-corp.co", "Lookalike Domain", CRIMSON),
    ("REPLY-TO", "r.sterling.wire@fin-gate.net", "Rogue Receiver", CRIMSON),
    ("DKIM ALIGN", "d=mail-bulkrelay.top", "Misaligned Sig", AMBER),
    ("DMARC POLICY", "p=none (Softfail)", "Bypass Active", AMBER),
    ("RETURN-PATH", "bounce@mal-infra-relay.ru", "Offshore Relay", CRIMSON),
    ("SENDING IP", "185.220.101.5 (AS49453)", "CyberBunker", CRIMSON),
]

add_text_box(slide, Inches(1.0), Inches(3.7), Inches(3.4), Inches(0.25),
             "DISCREPANCY HIERARCHY TREE", font_size=8, color=TEXT_MUTED, font_name="Consolas")
for i, (field, value, tag, color) in enumerate(discrepancies):
    yy = Inches(4.0 + i * 0.4)
    add_rect(slide, Inches(1.0), yy, Inches(3.4), Inches(0.35), fill_color=SURFACE_02, border_color=STROKE_M, border_width=Pt(0.5))
    add_text_box(slide, Inches(1.1), yy + Inches(0.03), Inches(1.0), Inches(0.25),
                 field, font_size=7, color=TEXT_MUTED, font_name="Consolas")
    add_text_box(slide, Inches(2.1), yy + Inches(0.03), Inches(1.3), Inches(0.25),
                 value, font_size=7, color=color, bold=True, font_name="Consolas")
    add_text_box(slide, Inches(3.5), yy + Inches(0.03), Inches(0.8), Inches(0.25),
                 tag, font_size=6, color=color, alignment=PP_ALIGN.RIGHT, font_name="Consolas")

# Right — Contradiction Alerts
add_rect(slide, Inches(4.9), Inches(1.7), Inches(7.6), Inches(5.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(5.1), Inches(1.85), Inches(7.2), Inches(0.3),
             "CONTRADICTION ALERT STACK  |  4 FLAGGED", font_size=10, color=CRIMSON, bold=True, font_name="Consolas")

alerts = [
    ("IC-01", "Reply-To Routing Divergence", "HIGH RISK",
     "Mismatch between RFC 5322 From domain and Reply-To header. Inbound replies steer to external adversarial endpoint. Conf: 96%", CRIMSON),
    ("IC-02", "C-Suite Impersonation", "CRITICAL",
     "Display name mirrors Robert Sterling (CFO) while transmitting from unauthorized external infrastructure. Target: Executive Wire Auth.", CRIMSON),
    ("IC-03", "Rogue Hosting Return-Path", "HIGH RISK",
     "Return-Path bounce destination resolved to Eastern European untrusted host notorious for bulletproof hosting and BEC operations. Geo: AS49453", CRIMSON),
    ("IC-04", "Lookalike Homoglyph Domain", "SUSPICIOUS",
     "Sender domain acme-corp.co has Levenshtein distance of 1 against authoritative acme-corp.com. WHOIS Age: 6d 04h.", AMBER),
]

for i, (code, title, severity, desc, color) in enumerate(alerts):
    yy = Inches(2.3 + i * 1.15)
    add_rect(slide, Inches(5.1), yy, Inches(7.2), Inches(1.0), fill_color=SURFACE_02, border_color=color, border_width=Pt(1))
    add_rect(slide, Inches(5.1), yy, Inches(0.55), Inches(1.0), fill_color=color)
    add_text_box(slide, Inches(5.1), yy + Inches(0.3), Inches(0.55), Inches(0.3),
                 code, font_size=8, color=BG_DARK, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
    add_text_box(slide, Inches(5.8), yy + Inches(0.08), Inches(4.5), Inches(0.3),
                 title, font_size=13, color=TEXT_HIGH, bold=True, font_name="Calibri")
    add_text_box(slide, Inches(10.8), yy + Inches(0.08), Inches(1.3), Inches(0.25),
                 severity, font_size=8, color=color, bold=True, alignment=PP_ALIGN.RIGHT, font_name="Consolas")
    add_text_box(slide, Inches(5.8), yy + Inches(0.42), Inches(6.4), Inches(0.5),
                 desc, font_size=10, color=TEXT_SUPPORT, font_name="Calibri")

add_slide_number(slide, 9, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — UI/UX OVERVIEW: INVESTIGATION GRAPH
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "UI/UX: Investigation Graph", "Correlation topology — 14-node multi-vector threat nexus")
add_footer_bar(slide)

# Left — Graph visualization placeholder
add_rect(slide, Inches(0.8), Inches(1.7), Inches(7.0), Inches(5.1), fill_color=NEAR_BLACK, border_color=STROKE_M)
add_text_box(slide, Inches(1.0), Inches(1.85), Inches(6.6), Inches(0.3),
             "CORRELATION TOPOLOGY  |  14 NODES  |  APEX-WIRE-FIN9 CLUSTER", font_size=9, color=CYAN, bold=True, font_name="Consolas")

# Simulated graph nodes
graph_nodes = [
    (3.5, 3.0, "EML-1042-A", "Target Wire Fraud", CYAN, 44),
    (2.0, 2.2, "R. Sterling", "Spoofed CFO", EMERALD, 32),
    (5.2, 2.2, "acme-corp.co", "Typosquat", COBALT, 32),
    (3.5, 4.5, "185.220.101.5", "AS49453 Bulletproof", CRIMSON, 40),
    (2.0, 5.2, "wire-verif.biz", "Phish Portal", AMBER, 28),
    (5.2, 5.2, "Campaign #17", "Apex Wire BEC", RGBColor(0xAC, 0xED, 0xFF), 32),
    (1.5, 3.5, "#EML-0988-B", "", CYAN, 24),
    (5.5, 3.5, "#EML-1011-C", "", CYAN, 24),
    (3.5, 1.8, "acme-corp.com", "Genuine", EMERALD, 28),
]

for x_in, y_in, label, sublabel, color, size in graph_nodes:
    x = Inches(x_in)
    y = Inches(y_in)
    sz = int(size * 0.9)
    # Node circle
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, Pt(sz), Pt(sz))
    shape.fill.solid()
    shape.fill.fore_color.rgb = SURFACE_02
    shape.line.color.rgb = color
    shape.line.width = Pt(1.5)
    # Label
    add_text_box(slide, x - Inches(0.3), y + Pt(sz) + Inches(0.02), Inches(1.2), Inches(0.3),
                 label, font_size=7, color=color, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
    if sublabel:
        add_text_box(slide, x - Inches(0.3), y + Pt(sz) + Inches(0.18), Inches(1.2), Inches(0.2),
                     sublabel, font_size=6, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Edge labels
edges = [
    (2.8, 2.55, "SPOOFS", TEXT_MUTED),
    (4.5, 2.55, "RESOLVES TO", TEXT_MUTED),
    (3.5, 3.75, "SENDS VIA", CRIMSON),
    (2.5, 4.85, "SHARES HOSTING", TEXT_MUTED),
    (4.8, 4.85, "ATTRIBUTED TO", CRIMSON),
]
for ex, ey, elabel, ecolor in edges:
    add_text_box(slide, Inches(ex), Inches(ey), Inches(1.2), Inches(0.15),
                 elabel, font_size=5, color=ecolor, alignment=PP_ALIGN.CENTER, font_name="Consolas")

# Legend
add_rect(slide, Inches(1.0), Inches(6.2), Inches(3.5), Inches(0.35), fill_color=SURFACE_01, border_color=STROKE_M, border_width=Pt(0.5))
legend_items = [("HOSTILE", CRIMSON), ("CORE", CYAN), ("VERIFIED", EMERALD)]
for i, (lbl, clr) in enumerate(legend_items):
    add_text_box(slide, Inches(1.1 + i * 1.1), Inches(6.22), Inches(1.0), Inches(0.25),
                 f"\u25CF {lbl}", font_size=7, color=clr, font_name="Consolas")

# Right — Entity Intel Panel
add_rect(slide, Inches(8.1), Inches(1.7), Inches(4.4), Inches(5.1), fill_color=SURFACE_01, border_color=CRIMSON, border_width=Pt(1))
add_text_box(slide, Inches(8.3), Inches(1.85), Inches(4.0), Inches(0.3),
             "SELECTED ENTITY INTEL", font_size=10, color=CYAN, bold=True, font_name="Consolas")

add_text_box(slide, Inches(8.3), Inches(2.3), Inches(4.0), Inches(0.2),
             "IP ADDRESS  |  HIGH RISK", font_size=9, color=CRIMSON, bold=True, font_name="Consolas")
add_text_box(slide, Inches(8.3), Inches(2.6), Inches(4.0), Inches(0.4),
             "185.220.101.5", font_size=20, color=TEXT_HIGH, bold=True, font_name="Consolas")
add_text_box(slide, Inches(8.3), Inches(3.05), Inches(2.5), Inches(0.3),
             "REPUTATION", font_size=8, color=TEXT_MUTED, font_name="Consolas")
add_text_box(slide, Inches(8.3), Inches(3.3), Inches(2.5), Inches(0.4),
             "94/100", font_size=24, color=CRIMSON, bold=True, font_name="Consolas")

intel_fields = [
    ("GEOLOCATION", "Frankfurt, DE"),
    ("AUTONOMOUS SYSTEM", "AS49453 (Bulletproof)"),
    ("CROSS-CASE CORRELATION", "Connected to 3 active fraud cases, 1 threat campaign, and 4 known financial lure templates in past 14 days."),
    ("SHA-256", "7f83b1657ff1fc53..."),
]
for i, (field, val) in enumerate(intel_fields):
    yy = Inches(3.9 + i * 0.7)
    add_text_box(slide, Inches(8.3), yy, Inches(4.0), Inches(0.2),
                 field, font_size=8, color=TEXT_MUTED, font_name="Consolas")
    add_text_box(slide, Inches(8.3), yy + Inches(0.2), Inches(4.0), Inches(0.4),
                 val, font_size=10, color=TEXT_HIGH, font_name="Calibri")

# Action buttons
add_rect(slide, Inches(8.3), Inches(6.2), Inches(4.0), Inches(0.45), fill_color=CYAN)
add_text_box(slide, Inches(8.3), Inches(6.23), Inches(4.0), Inches(0.4),
             "SEAL ARTIFACT INTO EVIDENCE VAULT", font_size=10, color=BG_DARK, bold=True,
             alignment=PP_ALIGN.CENTER, font_name="Calibri")

add_slide_number(slide, 10, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "System Architecture", "High-level forensic intelligence platform architecture")
add_footer_bar(slide)

# Architecture layers
layers = [
    ("1. EVIDENCE ACQUISITION", "MIME structure | Headers | Body | URLs | Attachments | Metadata | SHA-256", CYAN, Inches(1.7)),
    ("2. EVIDENCE NORMALIZATION", "RFC-aware parsing | Header canonicalization | Received-hop ordering | URL/Domain normalization", COBALT, Inches(2.6)),
    ("3. FORENSIC ENGINES", "Identity Contradiction | Infrastructure Fingerprint | Campaign Similarity | Evidence Reliability", CRIMSON, Inches(3.5)),
    ("4. INTELLIGENCE + AI", "Transformer NLP | XGBoost Structured ML | DNS/RDAP | IP/ASN/GeoIP | Threat Intelligence", AMBER, Inches(4.4)),
    ("5. CORRELATION", "Email | Domain | IP | ASN | URL | Identity | Related Emails | Campaign Discovery", EMERALD, Inches(5.3)),
    ("6. FORENSIC DECISION", "Threat Class | Risk | Confidence | Evidence Contribution | Attribution Hypothesis", RGBColor(0xAC, 0xED, 0xFF), Inches(6.2)),
]

for title, desc, color, y_pos in layers:
    add_rect(slide, Inches(0.8), y_pos, Inches(11.7), Inches(0.75), fill_color=SURFACE_01, border_color=color, border_width=Pt(1))
    add_rect(slide, Inches(0.8), y_pos, Inches(0.08), Inches(0.75), fill_color=color)
    add_text_box(slide, Inches(1.1), y_pos + Inches(0.08), Inches(4.0), Inches(0.3),
                 title, font_size=12, color=color, bold=True, font_name="Consolas")
    add_text_box(slide, Inches(1.1), y_pos + Inches(0.38), Inches(11.2), Inches(0.3),
                 desc, font_size=10, color=TEXT_SUPPORT, font_name="Calibri")

# Storage sidebar
add_rect(slide, Inches(10.8), Inches(1.7), Inches(1.7), Inches(0.75), fill_color=SURFACE_02, border_color=STROKE_M, border_width=Pt(0.5))
add_text_box(slide, Inches(10.8), Inches(1.8), Inches(1.7), Inches(0.2),
             "STORAGE", font_size=7, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER, font_name="Consolas")
add_text_box(slide, Inches(10.8), Inches(2.0), Inches(1.7), Inches(0.2),
             "PostgreSQL", font_size=8, color=EMERALD, alignment=PP_ALIGN.CENTER, font_name="Consolas")
add_text_box(slide, Inches(10.8), Inches(2.2), Inches(1.7), Inches(0.2),
             "Neo4j + MinIO", font_size=8, color=COBALT, alignment=PP_ALIGN.CENTER, font_name="Consolas")

# Output
add_rect(slide, Inches(0.8), Inches(6.2), Inches(9.8), Inches(0.75), fill_color=SURFACE_02, border_color=EMERALD, border_width=Pt(1.5))
add_text_box(slide, Inches(1.0), Inches(6.25), Inches(9.4), Inches(0.2),
             "OUTPUT: INVESTIGATION CASE", font_size=10, color=EMERALD, bold=True, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(6.55), Inches(9.4), Inches(0.3),
             "Timeline | Graph | Map | Evidence Package | Related Campaigns | Forensic Report | Chain of Custody",
             font_size=10, color=TEXT_HIGH, font_name="Calibri")

add_slide_number(slide, 11, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — TECHNOLOGY STACK
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Technology Stack", "Technologies supported by project references")
add_footer_bar(slide)

stack_categories = [
    ("LANGUAGES", ["Python", "TypeScript", "SQL", "Cypher"], CYAN),
    ("BACKEND", ["FastAPI", "Python email/MIME", "RFC-aware analysis"], COBALT),
    ("AI / ML", ["Transformer NLP", "XGBoost", "SHAP (Explainability)"], AMBER),
    ("DATABASE", ["PostgreSQL", "Neo4j + Cypher", "MinIO (Object Store)"], EMERALD),
    ("FRONTEND", ["React + TypeScript", "Leaflet (Maps)", "React Flow (Graphs)"], RGBColor(0xAC, 0xED, 0xFF)),
    ("INTELLIGENCE", ["VirusTotal", "AbuseIPDB", "RDAP / DNS / GeoIP"], CRIMSON),
    ("REPORTING", ["ReportLab (PDF)", "SHA-256 Integrity", "Chain of Custody"], TEXT_HIGH),
    ("DEPLOYMENT", ["Docker Compose", "Containerized Services", "Modular Architecture"], TEXT_SUPPORT),
]

for i, (cat_name, items, color) in enumerate(stack_categories):
    col = i % 4
    row = i // 4
    x = Inches(0.8 + col * 3.1)
    y = Inches(1.7 + row * 2.8)
    add_rect(slide, x, y, Inches(2.8), Inches(2.5), fill_color=SURFACE_01, border_color=color, border_width=Pt(1))
    add_rect(slide, x, y, Inches(2.8), Inches(0.4), fill_color=color)
    add_text_box(slide, x, y + Inches(0.05), Inches(2.8), Inches(0.3),
                 cat_name, font_size=10, color=BG_DARK, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
    for j, item in enumerate(items):
        add_text_box(slide, x + Inches(0.2), y + Inches(0.6 + j * 0.45), Inches(2.4), Inches(0.35),
                     f"\u25B8  {item}", font_size=12, color=TEXT_HIGH, font_name="Calibri")

add_slide_number(slide, 12, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — GRAPH DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Graph Data Model", "Neo4j entity-relationship model for forensic correlation")
add_footer_bar(slide)

# Entities
add_rect(slide, Inches(0.8), Inches(1.7), Inches(5.5), Inches(5.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(1.0), Inches(1.85), Inches(5.1), Inches(0.3),
             "GRAPH ENTITIES", font_size=10, color=COBALT, bold=True, font_name="Consolas")

entities = ["EMAIL", "PERSON / IDENTITY", "DOMAIN", "IP", "URL", "ASN", "ORGANIZATION", "CAMPAIGN", "CASE", "ATTACHMENT", "INCIDENT"]
entity_colors = [CYAN, EMERALD, COBALT, CRIMSON, AMBER, TEXT_HIGH, TEXT_SUPPORT, RGBColor(0xAC, 0xED, 0xFF), EMERALD, TEXT_MUTED, CRIMSON]
for i, (ent, clr) in enumerate(zip(entities, entity_colors)):
    yy = Inches(2.3 + i * 0.4)
    add_rect(slide, Inches(1.0), yy, Inches(1.8), Inches(0.32), fill_color=SURFACE_02, border_color=clr, border_width=Pt(0.75))
    add_text_box(slide, Inches(1.0), yy + Inches(0.03), Inches(1.8), Inches(0.25),
                 ent, font_size=9, color=clr, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")

# Relationships
add_rect(slide, Inches(6.6), Inches(1.7), Inches(5.9), Inches(5.1), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(6.8), Inches(1.85), Inches(5.5), Inches(0.3),
             "KEY RELATIONSHIPS", font_size=10, color=EMERALD, bold=True, font_name="Consolas")

relationships = [
    "EMAIL  \u2192  SENT_BY  \u2192  IDENTITY",
    "EMAIL  \u2192  USES  \u2192  DOMAIN",
    "EMAIL  \u2192  CONTAINS  \u2192  URL",
    "EMAIL  \u2192  ORIGINATED_FROM  \u2192  IP",
    "IP  \u2192  BELONGS_TO  \u2192  ASN",
    "DOMAIN  \u2192  RESOLVES_TO  \u2192  IP",
    "EMAIL  \u2192  PART_OF  \u2192  CAMPAIGN",
    "EMAIL  \u2192  RELATED_TO  \u2192  EMAIL",
    "DOMAIN  \u2192  RELATED_TO  \u2192  DOMAIN",
    "IP  \u2192  RELATED_TO  \u2192  IP",
    "CASE  \u2192  CONTAINS  \u2192  EMAIL",
]
for i, rel in enumerate(relationships):
    yy = Inches(2.3 + i * 0.4)
    add_text_box(slide, Inches(6.8), yy, Inches(5.5), Inches(0.35),
                 rel, font_size=10, color=TEXT_HIGH, font_name="Consolas")

# Campaign discovery callout
add_rect(slide, Inches(6.8), Inches(6.0), Inches(5.5), Inches(0.6), fill_color=SURFACE_02, border_color=EMERALD, border_width=Pt(1))
add_text_box(slide, Inches(7.0), Inches(6.05), Inches(5.1), Inches(0.5),
             "Campaign Discovery: Multiple emails sharing domains, IPs, URLs, language, identity, timing, "
             "and hosting are clustered into threat campaigns. This transforms the system from an email "
             "classifier into an investigation platform.",
             font_size=10, color=EMERALD, font_name="Calibri")

add_slide_number(slide, 13, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — INNOVATION / UNIQUENESS
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Innovation & Uniqueness", "What makes this different from existing solutions")
add_footer_bar(slide)

# Top callout
add_rect(slide, Inches(0.8), Inches(1.7), Inches(11.7), Inches(1.0), fill_color=SURFACE_01, border_color=EMERALD, border_width=Pt(1.5))
add_text_box(slide, Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.8),
             "The technology stack is NOT the innovation. The innovation is the COMBINATION of forensic reasoning "
             "engines that work together to provide evidence-driven investigative intelligence.",
             font_size=15, color=EMERALD, bold=True, font_name="Calibri")

# Innovation pillars
innovations = [
    ("Evidence Provenance", "Every finding has source, type, reliability, confidence, timestamp, supporting & contradicting relationships. Not just a threat score.", CYAN),
    ("Identity Contradiction", "Cross-references Display Name, From, Reply-To, Return-Path, DKIM domain, DMARC alignment, and infrastructure. Calculates identity consistency.", CRIMSON),
    ("Infrastructure Fingerprinting", "Builds complete profiles: IP -> ASN -> ISP -> Hosting -> DNS -> Domain -> MX. Identifies VPN, TOR, proxy, bulletproof hosting.", AMBER),
    ("Campaign Discovery", "Correlates multiple emails into threat campaigns using shared infrastructure, language, identity, timing, and hosting patterns.", COBALT),
    ("Evidence Reliability", "Distinguishes HIGH/MEDIUM/LOWER confidence. Explains what is directly observed vs inferred vs externally enriched vs uncertain.", EMERALD),
    ("Attack Path Reconstruction", "Reconstructs observed chain from sender identity through infrastructure to related cases. Shows observed vs inferred vs uncertain.", RGBColor(0xAC, 0xED, 0xFF)),
    ("Explainable Multi-Evidence Decision", "Combines technical, identity, linguistic, infrastructure, historical, and relationship evidence into a single explainable forensic decision.", TEXT_HIGH),
    ("Forensic Accuracy", "Never claims attacker location or identity. Uses language like 'observed sending infrastructure geolocates to...' not 'attacker is in...'", TEXT_SUPPORT),
]

for i, (title, desc, color) in enumerate(innovations):
    col = i % 2
    row = i // 2
    x = Inches(0.8 + col * 6.0)
    y = Inches(3.0 + row * 1.1)
    add_rect(slide, x, y, Inches(5.7), Inches(0.95), fill_color=SURFACE_01, border_color=color, border_width=Pt(1))
    add_rect(slide, x, y, Inches(0.06), Inches(0.95), fill_color=color)
    add_text_box(slide, x + Inches(0.2), y + Inches(0.05), Inches(5.3), Inches(0.3),
                 title, font_size=13, color=color, bold=True, font_name="Calibri")
    add_text_box(slide, x + Inches(0.2), y + Inches(0.38), Inches(5.3), Inches(0.5),
                 desc, font_size=10, color=TEXT_SUPPORT, font_name="Calibri")

add_slide_number(slide, 14, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 15 — DEMO SCENARIO
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Demo Scenario", "CFO BEC Attack — Case #1042 Walkthrough")
add_footer_bar(slide)

# Scenario description
add_rect(slide, Inches(0.8), Inches(1.7), Inches(11.7), Inches(1.2), fill_color=SURFACE_01, border_color=CRIMSON, border_width=Pt(1.5))
add_text_box(slide, Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.25),
             "SCENARIO: SUSPICIOUS CFO PAYMENT-REQUEST EMAIL", font_size=10, color=CRIMSON, bold=True, font_name="Consolas")
add_text_box(slide, Inches(1.0), Inches(2.1), Inches(11.3), Inches(0.7),
             "An urgent wire transfer request appears to come from the CFO, Robert Sterling. The email requests immediate "
             "payment to a new offshore account. The analyst uploads the .EML file for forensic investigation.",
             font_size=13, color=TEXT_HIGH, font_name="Calibri")

# Demo steps
demo_steps = [
    ("01", "UPLOAD", "Upload suspicious\n.EML file", CYAN),
    ("02", "PRESERVE", "Calculate SHA-256\n& parse MIME", CYAN),
    ("03", "AUTHENTICATE", "SPF/DKIM/DMARC\nanalysis", AMBER),
    ("04", "IDENTITY", "Compare From vs\nReply-To vs DKIM", CRIMSON),
    ("05", "INFRASTRUCTURE", "IP/ASN/Hosting\nprofiling", AMBER),
    ("06", "INTELLIGENCE", "NLP/ML threat\nclassification", COBALT),
    ("07", "CORRELATE", "Graph building\n& campaign search", EMERALD),
    ("08", "DECIDE", "Risk + Confidence\n+ Evidence weights", CRIMSON),
    ("09", "ATTACK PATH", "Reconstruct\nobserved chain", AMBER),
    ("10", "REPORT", "Forensic PDF\nwith chain-of-custody", EMERALD),
]

for i, (num, label, detail, color) in enumerate(demo_steps):
    x = Inches(0.65 + i * 1.25)
    y = Inches(3.2)
    add_rect(slide, x, y, Inches(1.1), Inches(1.8), fill_color=SURFACE_02, border_color=color, border_width=Pt(1))
    add_rect(slide, x, y, Inches(1.1), Inches(0.35), fill_color=color)
    add_text_box(slide, x, y + Inches(0.03), Inches(1.1), Inches(0.3),
                 num, font_size=12, color=BG_DARK, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
    add_text_box(slide, x, y + Inches(0.45), Inches(1.1), Inches(0.3),
                 label, font_size=9, color=color, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")
    add_text_box(slide, x, y + Inches(0.8), Inches(1.1), Inches(0.8),
                 detail, font_size=8, color=TEXT_SUPPORT, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Expected findings
add_rect(slide, Inches(0.8), Inches(5.3), Inches(11.7), Inches(1.6), fill_color=SURFACE_01, border_color=STROKE_M)
add_text_box(slide, Inches(1.0), Inches(5.4), Inches(5.5), Inches(0.25),
             "EXPECTED FINDINGS", font_size=10, color=CRIMSON, bold=True, font_name="Consolas")

findings_left = [
    ("Threat Classification", "BEC — Executive Impersonation"),
    ("Risk Score", "91/100 (Critical)"),
    ("Identity Consistency", "34/100 (High Contradiction)"),
    ("Campaign", "Cluster #17 — 3 related emails"),
]
for i, (label, val) in enumerate(findings_left):
    yy = Inches(5.75 + i * 0.25)
    add_text_box(slide, Inches(1.0), yy, Inches(2.0), Inches(0.22),
                 label, font_size=9, color=TEXT_MUTED, font_name="Calibri")
    add_text_box(slide, Inches(3.0), yy, Inches(3.0), Inches(0.22),
                 val, font_size=9, color=TEXT_HIGH, bold=True, font_name="Calibri")

findings_right = [
    ("Contradictions", "Reply-To mismatch, Lookalike domain, Executive impersonation, Bulletproof VPS"),
    ("Infrastructure", "185.220.101.5 (AS49453 CyberBunker) -> acme-corp.co -> wire-verif.biz"),
    ("Authentication", "SPF PASS (soft-aligned) | DKIM PASS (third-party) | DMARC NONE (p=none policy exploited)"),
    ("Confidence", "Model: 89.4% | Evidence: 87.1% | Non-Repudiation: Assured"),
]
for i, (label, val) in enumerate(findings_right):
    yy = Inches(5.75 + i * 0.25)
    add_text_box(slide, Inches(6.5), yy, Inches(1.5), Inches(0.22),
                 label, font_size=9, color=TEXT_MUTED, font_name="Calibri")
    add_text_box(slide, Inches(8.0), yy, Inches(4.3), Inches(0.22),
                 val, font_size=9, color=TEXT_HIGH, font_name="Calibri")

add_slide_number(slide, 15, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 16 — EXPECTED IMPACT
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Expected Impact", "Measurable benefits for cybersecurity investigation")
add_footer_bar(slide)

impacts = [
    ("Faster Investigation", "Reduces email forensic analysis from hours/days to minutes. Automated evidence extraction, normalization, and correlation accelerate triage.", CYAN),
    ("Campaign Discovery", "Transforms single-email classification into campaign-level intelligence. Detects coordinated attacks across multiple incidents.", COBALT),
    ("Evidence Defensibility", "Forensic-grade evidence with chain-of-custody, SHA-256 integrity, and provenance tracking. Legally defensible for prosecution.", EMERALD),
    ("Reduced False Positives", "Multi-evidence decision engine with explainable reasoning reduces false positive alerts. Analysts can verify every finding.", AMBER),
    ("Cross-Case Intelligence", "Graph-based correlation discovers related incidents, shared infrastructure, and threat campaigns across the organization's case history.", CRIMSON),
    ("Operational Efficiency", "Single platform replacing fragmented tools. Investigative workbench with graph, map, timeline, and report generation in one interface.", RGBColor(0xAC, 0xED, 0xFF)),
]

for i, (title, desc, color) in enumerate(impacts):
    col = i % 2
    row = i // 2
    x = Inches(0.8 + col * 6.0)
    y = Inches(1.7 + row * 1.8)
    add_rect(slide, x, y, Inches(5.7), Inches(1.55), fill_color=SURFACE_01, border_color=color, border_width=Pt(1))
    add_rect(slide, x, y, Inches(0.06), Inches(1.55), fill_color=color)
    add_text_box(slide, x + Inches(0.2), y + Inches(0.1), Inches(5.3), Inches(0.35),
                 title, font_size=16, color=color, bold=True, font_name="Calibri")
    add_text_box(slide, x + Inches(0.2), y + Inches(0.55), Inches(5.3), Inches(0.9),
                 desc, font_size=12, color=TEXT_SUPPORT, font_name="Calibri")

add_slide_number(slide, 16, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 17 — SCALABILITY / FUTURE SCOPE
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Scalability & Future Scope", "Platform evolution roadmap")
add_footer_bar(slide)

# Phase 1 — MVP
add_rect(slide, Inches(0.8), Inches(1.7), Inches(3.7), Inches(5.1), fill_color=SURFACE_01, border_color=CYAN, border_width=Pt(1.5))
add_rect(slide, Inches(0.8), Inches(1.7), Inches(3.7), Inches(0.5), fill_color=CYAN)
add_text_box(slide, Inches(0.8), Inches(1.75), Inches(3.7), Inches(0.4),
             "PHASE 1: MVP (Hackathon)", font_size=12, color=BG_DARK, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")

mvp_items = [
    "Email ingestion & MIME parsing",
    "SPF/DKIM/DMARC analysis",
    "Identity contradiction detection",
    "IP/ASN/GeoIP profiling",
    "NLP-based BEC detection",
    "XGBoost structured classification",
    "Neo4j graph construction",
    "Investigation dashboard UI",
    "Forensic PDF report generation",
    "Case management basics",
]
for i, item in enumerate(mvp_items):
    add_text_box(slide, Inches(1.0), Inches(2.4 + i * 0.35), Inches(3.3), Inches(0.3),
                 f"\u2713  {item}", font_size=11, color=TEXT_HIGH, font_name="Calibri")

# Phase 2
add_rect(slide, Inches(4.8), Inches(1.7), Inches(3.7), Inches(5.1), fill_color=SURFACE_01, border_color=AMBER, border_width=Pt(1))
add_rect(slide, Inches(4.8), Inches(1.7), Inches(3.7), Inches(0.5), fill_color=AMBER)
add_text_box(slide, Inches(4.8), Inches(1.75), Inches(3.7), Inches(0.4),
             "PHASE 2: Enhanced", font_size=12, color=BG_DARK, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")

phase2_items = [
    "Campaign discovery engine",
    "Attack path reconstruction",
    "Blockchain evidence integrity",
    "Advanced NLP fine-tuning",
    "Real-time email feed monitoring",
    "Multi-tenant deployment",
    "API for third-party integration",
    "Automated alerting system",
    "Interactive graph visualization",
    "Mobile-responsive UI",
]
for i, item in enumerate(phase2_items):
    add_text_box(slide, Inches(5.0), Inches(2.4 + i * 0.35), Inches(3.3), Inches(0.3),
                 f"\u25B8  {item}", font_size=11, color=TEXT_HIGH, font_name="Calibri")

# Phase 3
add_rect(slide, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.1), fill_color=SURFACE_01, border_color=EMERALD, border_width=Pt(1))
add_rect(slide, Inches(8.8), Inches(1.7), Inches(3.7), Inches(0.5), fill_color=EMERALD)
add_text_box(slide, Inches(8.8), Inches(1.75), Inches(3.7), Inches(0.4),
             "PHASE 3: Enterprise", font_size=12, color=BG_DARK, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")

phase3_items = [
    "Distributed processing (Kafka)",
    "Kubernetes orchestration",
    "Elasticsearch full-text search",
    "SIEM/SOAR integrations",
    "Advanced attribution models",
    "Threat intelligence sharing (STIX/TAXII)",
    "Compliance reporting (NIST, ISO)",
    "Multi-language email support",
    "Federated learning for privacy",
    "Global campaign tracking",
]
for i, item in enumerate(phase3_items):
    add_text_box(slide, Inches(9.0), Inches(2.4 + i * 0.35), Inches(3.3), Inches(0.3),
                 f"\u25B8  {item}", font_size=11, color=TEXT_HIGH, font_name="Calibri")

add_slide_number(slide, 17, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 18 — IMPLEMENTATION FEASIBILITY
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)
add_section_header(slide, "Implementation Feasibility", "Realistic hackathon implementation plan")
add_footer_bar(slide)

# Team & Timeline
add_rect(slide, Inches(0.8), Inches(1.7), Inches(5.7), Inches(2.2), fill_color=SURFACE_01, border_color=CYAN, border_width=Pt(1))
add_text_box(slide, Inches(1.0), Inches(1.85), Inches(5.3), Inches(0.3),
             "TEAM COMPOSITION", font_size=10, color=CYAN, bold=True, font_name="Consolas")

team_roles = [
    ("Backend Engineer", "FastAPI, email parsing, forensic engines", CYAN),
    ("ML Engineer", "NLP model, XGBoost, SHAP explainability", AMBER),
    ("Frontend Engineer", "React + TypeScript dashboard, graph viz", COBALT),
    ("Graph / Data Engineer", "Neo4j, correlation, campaign discovery", EMERALD),
    ("Security Researcher", "Email forensics, threat intel APIs", CRIMSON),
]
for i, (role, desc, color) in enumerate(team_roles):
    yy = Inches(2.3 + i * 0.32)
    add_text_box(slide, Inches(1.0), yy, Inches(2.0), Inches(0.25),
                 role, font_size=10, color=color, bold=True, font_name="Calibri")
    add_text_box(slide, Inches(3.0), yy, Inches(3.3), Inches(0.25),
                 desc, font_size=9, color=TEXT_SUPPORT, font_name="Calibri")

# Implementation strategy
add_rect(slide, Inches(6.8), Inches(1.7), Inches(5.7), Inches(2.2), fill_color=SURFACE_01, border_color=AMBER, border_width=Pt(1))
add_text_box(slide, Inches(7.0), Inches(1.85), Inches(5.3), Inches(0.3),
             "IMPLEMENTATION STRATEGY", font_size=10, color=AMBER, bold=True, font_name="Consolas")

strategies = [
    ("Modular Architecture", "Independent engines can be developed in parallel"),
    ("Docker Compose", "One-command deployment for all services"),
    ("Mock External APIs", "VirusTotal/AbuseIPDB mocks for hackathon demo"),
    ("Real .EML Processing", "Actual email parsing, not simulated data"),
    ("Incremental Integration", "Build engines first, wire together last"),
]
for i, (strat, desc) in enumerate(strategies):
    yy = Inches(2.3 + i * 0.32)
    add_text_box(slide, Inches(7.0), yy, Inches(2.2), Inches(0.25),
                 strat, font_size=10, color=EMERALD, bold=True, font_name="Calibri")
    add_text_box(slide, Inches(9.2), yy, Inches(3.1), Inches(0.25),
                 desc, font_size=9, color=TEXT_SUPPORT, font_name="Calibri")

# Key risks & mitigations
add_rect(slide, Inches(0.8), Inches(4.2), Inches(5.7), Inches(2.6), fill_color=SURFACE_01, border_color=CRIMSON, border_width=Pt(1))
add_text_box(slide, Inches(1.0), Inches(4.35), Inches(5.3), Inches(0.3),
             "KEY RISKS & MITIGATIONS", font_size=10, color=CRIMSON, bold=True, font_name="Consolas")

risks = [
    ("Complex ML pipeline", "Use pre-trained models + fine-tuning on synthetic data"),
    ("Neo4j graph complexity", "Start with core entities, expand incrementally"),
    ("API rate limits", "Mock external APIs for demo, real keys for validation"),
    ("UI polish time", "Use Stitch design system for rapid consistent UI"),
    ("Integration risk", "Define API contracts early, parallel development"),
]
for i, (risk, mitigation) in enumerate(risks):
    yy = Inches(4.7 + i * 0.38)
    add_text_box(slide, Inches(1.0), yy, Inches(2.2), Inches(0.3),
                 f"\u26A0  {risk}", font_size=10, color=AMBER, font_name="Calibri")
    add_text_box(slide, Inches(3.2), yy, Inches(3.1), Inches(0.3),
                 f"\u2713  {mitigation}", font_size=10, color=EMERALD, font_name="Calibri")

# Proof of concept
add_rect(slide, Inches(6.8), Inches(4.2), Inches(5.7), Inches(2.6), fill_color=SURFACE_01, border_color=EMERALD, border_width=Pt(1))
add_text_box(slide, Inches(7.0), Inches(4.35), Inches(5.3), Inches(0.3),
             "PROOF OF CONCEPT", font_size=10, color=EMERALD, bold=True, font_name="Consolas")

poc_items = [
    ("Demo Email", "Pre-built CFO BEC scenario (.EML file)"),
    ("Working Pipeline", "Upload -> Parse -> Analyze -> Correlate -> Report"),
    ("Live Dashboard", "Stitch-designed UI with real-time analysis results"),
    ("Graph Visualization", "Neo4j-backed entity correlation graph"),
    ("Forensic Report", "PDF with full evidence chain and confidence scores"),
    ("Hash Verification", "SHA-256 integrity check with chain-of-custody"),
]
for i, (item, desc) in enumerate(poc_items):
    yy = Inches(4.7 + i * 0.32)
    add_text_box(slide, Inches(7.0), yy, Inches(1.5), Inches(0.25),
                 item, font_size=10, color=CYAN, bold=True, font_name="Calibri")
    add_text_box(slide, Inches(8.5), yy, Inches(3.8), Inches(0.25),
                 desc, font_size=10, color=TEXT_HIGH, font_name="Calibri")

add_slide_number(slide, 18, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 19 — THANK YOU / Q&A
# ═══════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
dark_bg(slide)

# Top accent bar
add_rect(slide, Inches(0), Inches(0), W, Inches(0.06), fill_color=CYAN)

# Center content
add_rect(slide, Inches(2.5), Inches(2.0), Inches(8.3), Inches(3.8), fill_color=SURFACE_01, border_color=STROKE_M)

# SIH badge
add_rect(slide, Inches(5.0), Inches(2.3), Inches(3.3), Inches(0.5), fill_color=SURFACE_02, border_color=CYAN)
add_text_box(slide, Inches(5.0), Inches(2.33), Inches(3.3), Inches(0.4),
             "SIH26106", font_size=14, color=CYAN, bold=True, alignment=PP_ALIGN.CENTER, font_name="Consolas")

# Thank you
add_text_box(slide, Inches(2.5), Inches(3.0), Inches(8.3), Inches(0.8),
             "Thank You", font_size=44, color=TEXT_HIGH, bold=True, alignment=PP_ALIGN.CENTER, font_name="Calibri")

add_accent_line(slide, Inches(5.0), Inches(3.85), Inches(3.3), CYAN)

add_text_box(slide, Inches(2.5), Inches(4.05), Inches(8.3), Inches(0.6),
             "AI-Powered Email Forensic Intelligence Platform",
             font_size=16, color=TEXT_SUPPORT, alignment=PP_ALIGN.CENTER, font_name="Calibri")

add_text_box(slide, Inches(2.5), Inches(4.55), Inches(8.3), Inches(0.5),
             "Questions & Discussion",
             font_size=14, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER, font_name="Calibri")

# Key takeaways
add_rect(slide, Inches(1.5), Inches(6.0), Inches(10.3), Inches(1.0), fill_color=SURFACE_02, border_color=STROKE_M, border_width=Pt(0.5))
takeaways = [
    "Evidence-driven forensic reasoning, not generic email classification",
    "Identity contradiction + campaign discovery + attack path reconstruction",
    "Explainable multi-evidence decisions with confidence and provenance",
]
for i, t in enumerate(takeaways):
    add_text_box(slide, Inches(1.8), Inches(6.1 + i * 0.25), Inches(9.7), Inches(0.22),
                 f"\u25B8  {t}", font_size=11, color=TEXT_HIGH, font_name="Calibri")

# Bottom bar
add_rect(slide, Inches(0), Inches(7.15), W, Inches(0.35), fill_color=SURFACE_01)
add_text_box(slide, Inches(0.5), Inches(7.17), Inches(5), Inches(0.3),
             "TraceMail  |  Forensic Email Evidence Engine  |  SIH26106", font_size=9, color=TEXT_MUTED)

add_slide_number(slide, 19, TOTAL_SLIDES)

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════════
output_path = r"C:\SIH\SIH_Hackathon_Presentation.pptx"
prs.save(output_path)
print(f"Presentation saved: {output_path}")
print(f"Total slides: {TOTAL_SLIDES}")
