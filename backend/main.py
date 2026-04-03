"""
main.py — FastAPI backend for PropagandaLens.

Routes:
  POST /analyze           — Analyze text for propaganda techniques
  POST /chat              — Chat about the analysis
  POST /timeline          — Multi-document temporal analysis
  GET  /export/pdf/{id}   — Download PDF report
  POST /upload            — Upload .txt or .pdf file, returns extracted text
  GET  /health            — Health check
"""

import io
import os
import json
import uuid
import logging
import textwrap
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from analyzer import analyze_text
from groq_chat import chat as groq_chat, SUGGESTED_PROMPTS
from timeline import analyze_timeline

# PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PropagandaLens API",
    description="Multilingual Propaganda & Manipulation Detection API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for analysis results (keyed by analysis_id)
# In production, use Redis or a DB
_analysis_cache: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Text to analyze")


class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    analysis_id: str = Field(..., description="ID from a previous /analyze call")
    history: list[dict] = Field(default=[], description="Previous conversation turns")


class TimelineDocument(BaseModel):
    date: str = Field(..., description="ISO date string, e.g. 2024-01-15")
    text: str = Field(..., min_length=10)
    label: Optional[str] = None


class TimelineRequest(BaseModel):
    documents: list[TimelineDocument] = Field(..., min_length=1, max_length=20)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "PropagandaLens API", "version": "1.0.0"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """Analyze text for propaganda and manipulation techniques."""
    try:
        result = analyze_text(request.text)
        # Cache result
        _analysis_cache[result["analysis_id"]] = result
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/chat")
async def chat_endpoint(request: ChatMessage):
    """Chat about a previously analyzed text."""
    analysis_context = _analysis_cache.get(request.analysis_id)
    if not analysis_context:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Please run /analyze first.",
        )
    try:
        response = groq_chat(
            message=request.message,
            analysis_context=analysis_context,
            history=request.history,
        )
        return {
            "response": response,
            "suggested_prompts": SUGGESTED_PROMPTS[:3],
        }
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/timeline")
async def timeline_endpoint(request: TimelineRequest):
    """Analyze multiple documents over time."""
    try:
        docs = [d.model_dump() for d in request.documents]
        result = analyze_timeline(docs)
        return result
    except Exception as e:
        logger.error(f"Timeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a .txt or .pdf file and extract its text content."""
    filename = file.filename or ""
    content_type = file.content_type or ""

    if filename.endswith(".txt") or "text/plain" in content_type:
        raw = await file.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        return {"text": text, "filename": filename}

    elif filename.endswith(".pdf") or "pdf" in content_type:
        raw = await file.read()
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            pages_text = []
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")
            text = "\n\n".join(pages_text)
            return {"text": text, "filename": filename}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF extraction failed: {e}")

    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Please upload a .txt or .pdf file.",
        )


@app.get("/export/pdf/{analysis_id}")
async def export_pdf(analysis_id: str):
    """Generate and download a PDF report for a given analysis."""
    result = _analysis_cache.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    try:
        pdf_bytes = generate_pdf_report(result)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="propagandalens_report_{analysis_id[:8]}.pdf"'},
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

TECHNIQUE_COLORS_HEX = {
    "Fear Appeal": "#EF4444",
    "False Dilemma": "#F97316",
    "Loaded Language": "#EAB308",
    "Bandwagon": "#3B82F6",
    "Ad Hominem": "#8B5CF6",
    "Glittering Generalities": "#10B981",
    "Card Stacking": "#06B6D4",
    "Repetition": "#EC4899",
}


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def generate_pdf_report(result: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Title ---
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1e1b4b"),
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#374151"),
    )
    highlight_style = ParagraphStyle(
        "Highlight",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#111827"),
    )

    story.append(Paragraph("PropagandaLens Analysis Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')} | "
        f"Analysis ID: {result.get('analysis_id', 'N/A')[:8]}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 12))

    # --- Score Summary ---
    story.append(Paragraph("Executive Summary", heading_style))

    credibility = result.get("credibility", "Unknown")
    cred_colors = {
        "Trustworthy": "#10B981",
        "Biased": "#F97316",
        "Highly Manipulative": "#EF4444",
    }
    cred_color = cred_colors.get(credibility, "#6b7280")

    summary_data = [
        ["Metric", "Value"],
        ["Overall Manipulation Score", f"{result.get('overall_score', 0)}/100"],
        ["Credibility Rating", credibility],
        ["Detected Language", result.get("language", "en").upper()],
        ["Total Sentences Analyzed", str(result.get("sentence_count", 0))],
        ["Manipulative Sentences", str(result.get("manipulative_sentence_count", 0))],
        ["Processing Time", f"{result.get('processing_time_seconds', 0)}s"],
    ]
    summary_table = Table(summary_data, colWidths=[9 * cm, 7 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9fafb"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # --- Technique Breakdown ---
    story.append(Paragraph("Technique Breakdown", heading_style))
    breakdown = result.get("technique_breakdown", [])
    detected = [t for t in breakdown if t["count"] > 0]

    if detected:
        tech_data = [["Technique", "Occurrences", "Avg Confidence"]]
        for item in sorted(detected, key=lambda x: -x["avg_confidence"]):
            tech_data.append([
                item["technique"],
                str(item["count"]),
                f"{item['avg_confidence']:.0f}%",
            ])
        tech_table = Table(tech_data, colWidths=[9 * cm, 4 * cm, 4 * cm])
        tech_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9fafb"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tech_table)
    else:
        story.append(Paragraph("No manipulation techniques detected.", body_style))

    story.append(Spacer(1, 16))

    # --- Detected Spans ---
    story.append(Paragraph("Detected Manipulation Spans", heading_style))
    spans = result.get("spans", [])

    if spans:
        for i, span in enumerate(spans, 1):
            technique = span.get("technique", "Unknown")
            confidence = span.get("confidence", 0)
            explanation = span.get("explanation", "")
            text_snippet = span.get("text", "")[:300]
            color_hex = TECHNIQUE_COLORS_HEX.get(technique, "#9CA3AF")

            block = KeepTogether([
                Paragraph(
                    f'<b>{i}. {technique}</b> — <font color="{color_hex}">■</font> '
                    f'Confidence: {confidence}%',
                    highlight_style
                ),
                Paragraph(
                    f'<i>"{textwrap.shorten(text_snippet, width=200, placeholder="...")}"</i>',
                    ParagraphStyle("Quote", parent=body_style, leftIndent=12,
                                   textColor=colors.HexColor("#4b5563"), fontSize=9)
                ),
                Paragraph(
                    f'<b>Why:</b> {explanation}',
                    ParagraphStyle("Explain", parent=body_style, leftIndent=12, fontSize=9)
                ),
                Spacer(1, 8),
            ])
            story.append(block)
    else:
        story.append(Paragraph("No specific manipulative spans were detected.", body_style))

    # --- Analyzed Text ---
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Original Text", heading_style))
    original = result.get("original_text", "")
    story.append(Paragraph(
        textwrap.shorten(original, width=2000, placeholder="... [truncated]"),
        ParagraphStyle("OrigText", parent=body_style, fontSize=9, textColor=colors.HexColor("#6b7280"))
    ))

    doc.build(story)
    return buffer.getvalue()
