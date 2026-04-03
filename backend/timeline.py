"""
timeline.py — Temporal analysis for PropagandaLens.

Accepts multiple {date, text} documents and returns time-series
manipulation scores with per-technique breakdowns.
"""

import logging
from typing import Any
from analyzer import analyze_text, TECHNIQUES

logger = logging.getLogger(__name__)


def analyze_timeline(documents: list[dict]) -> dict:
    """
    Analyze multiple documents over time.
    
    Input: [{date: str, text: str, label?: str}, ...]
    Returns: {
        data_points: [{date, label, overall_score, credibility, technique_breakdown, dominant_technique}],
        technique_trends: {technique: [score_at_each_date]},
        summary: {most_manipulative_date, avg_score, dominant_technique_overall}
    }
    """
    if not documents:
        return {"data_points": [], "technique_trends": {}, "summary": {}}

    # Sort by date string (works for ISO dates YYYY-MM-DD)
    sorted_docs = sorted(documents, key=lambda d: d.get("date", ""))

    data_points = []
    technique_trends: dict[str, list[float]] = {t: [] for t in TECHNIQUES}
    all_scores = []

    technique_total_counts: dict[str, int] = {t: 0 for t in TECHNIQUES}

    for doc in sorted_docs:
        date = doc.get("date", "Unknown")
        text = doc.get("text", "")
        label = doc.get("label", f"Document ({date})")

        if not text.strip():
            logger.warning(f"Empty text for date {date}, skipping.")
            continue

        try:
            result = analyze_text(text)
        except Exception as e:
            logger.error(f"Analysis failed for date {date}: {e}")
            continue

        overall_score = result["overall_score"]
        credibility = result["credibility"]
        breakdown = result["technique_breakdown"]

        # Build per-technique scores for this doc
        per_technique = {item["technique"]: item["avg_confidence"] for item in breakdown}

        # Update trends
        for technique in TECHNIQUES:
            score = per_technique.get(technique, 0.0)
            technique_trends[technique].append(score)
            technique_total_counts[technique] += breakdown[TECHNIQUES.index(technique)]["count"]

        # Dominant technique this doc
        dominant = max(breakdown, key=lambda x: x["avg_confidence"])
        dominant_technique = dominant["technique"] if dominant["avg_confidence"] > 0 else None

        data_points.append({
            "date": date,
            "label": label,
            "overall_score": overall_score,
            "credibility": credibility,
            "technique_breakdown": breakdown,
            "dominant_technique": dominant_technique,
            "sentence_count": result["sentence_count"],
            "manipulative_count": result["manipulative_sentence_count"],
        })

        all_scores.append(overall_score)

    # Summary
    if data_points:
        most_manipulative = max(data_points, key=lambda d: d["overall_score"])
        avg_score = round(sum(all_scores) / len(all_scores), 1)
        overall_dominant = max(technique_total_counts, key=technique_total_counts.get)
    else:
        most_manipulative = None
        avg_score = 0
        overall_dominant = None

    return {
        "data_points": data_points,
        "technique_trends": technique_trends,
        "dates": [dp["date"] for dp in data_points],
        "summary": {
            "document_count": len(data_points),
            "avg_score": avg_score,
            "most_manipulative_date": most_manipulative["date"] if most_manipulative else None,
            "most_manipulative_score": most_manipulative["overall_score"] if most_manipulative else None,
            "dominant_technique_overall": overall_dominant,
        },
    }
