"""
analyzer.py — Core NLP pipeline for PropagandaLens.

Pipeline:
 1. Detect language (langdetect)
 2. Translate Hindi → English (Helsinki-NLP/opus-mt-hi-en) if needed
 3. Sentence tokenize (NLTK)
 4. Batch few-shot classification via Groq (llama-3.3-70b)
 5. Map spans back to original text character offsets
 6. Aggregate overall score & credibility rating
"""

import os
import re
import json
import uuid
import time
import logging
from typing import Optional

import nltk
from langdetect import detect, LangDetectException
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Download NLTK data silently on first run
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TECHNIQUES = [
    "Fear Appeal",
    "False Dilemma",
    "Loaded Language",
    "Bandwagon",
    "Ad Hominem",
    "Glittering Generalities",
    "Card Stacking",
    "Repetition",
]

TECHNIQUE_COLORS: dict[str, str] = {
    "Fear Appeal": "#EF4444",
    "False Dilemma": "#F97316",
    "Loaded Language": "#EAB308",
    "Bandwagon": "#3B82F6",
    "Ad Hominem": "#8B5CF6",
    "Glittering Generalities": "#10B981",
    "Card Stacking": "#06B6D4",
    "Repetition": "#EC4899",
}

CREDIBILITY_THRESHOLDS = {
    "Trustworthy": (0, 30),
    "Biased": (30, 60),
    "Highly Manipulative": (60, 101),
}

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = f"""You are a world-class propaganda and rhetorical manipulation detection expert.

You will be given a sentence. Analyze it strictly for the presence of ONE of these 8 manipulation techniques:
{', '.join(f'"{t}"' for t in TECHNIQUES)}

Definitions:
- Fear Appeal: Attempts to create fear or anxiety to manipulate behavior.
- False Dilemma: Presents only two options when more exist ("us or them", "either...or").
- Loaded Language: Uses emotionally charged words to sway opinion.
- Bandwagon: Appeals to popularity or the idea that everyone else is doing it.
- Ad Hominem: Attacks the person making an argument rather than the argument itself.
- Glittering Generalities: Uses vague, positive-sounding words without substance (freedom, hope, glory).
- Card Stacking: Selectively presents only evidence that supports one side.
- Repetition: Repeats a claim or phrase to hammer it into the audience's mind.

RULES:
- Return ONLY valid JSON. No markdown, no code fences, no explanation outside the JSON.
- If a technique IS detected, return:
  {{"technique": "<TechniqueName>", "confidence": <0-100 integer>, "explanation": "<one concise sentence explaining why>"}}
- If NO manipulation technique is detected, return:
  {{"technique": null, "confidence": 0, "explanation": ""}}
"""


# ---------------------------------------------------------------------------
# Translation (lazy-loaded)
# ---------------------------------------------------------------------------

_translator = None
_tokenizer = None


def _get_translator():
    global _translator, _tokenizer
    if _translator is None:
        from transformers import MarianMTModel, MarianTokenizer
        model_name = "Helsinki-NLP/opus-mt-hi-en"
        logger.info("Loading Helsinki-NLP translation model (first run may take a while)...")
        _tokenizer = MarianTokenizer.from_pretrained(model_name)
        _translator = MarianMTModel.from_pretrained(model_name)
        logger.info("Translation model loaded.")
    return _tokenizer, _translator


def translate_hi_to_en(text: str) -> str:
    """Translate Hindi text to English using Helsinki-NLP/opus-mt-hi-en."""
    tokenizer, model = _get_translator()
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)


# ---------------------------------------------------------------------------
# Groq classification
# ---------------------------------------------------------------------------

_groq_client: Optional[Groq] = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def classify_sentence(sentence: str) -> dict:
    """
    Run Groq few-shot classification on a single sentence.
    Returns: {technique, confidence, explanation}
    """
    client = _get_groq_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f'Analyze this sentence: "{sentence}"'},
            ],
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        # Validate technique name
        if result.get("technique") not in TECHNIQUES:
            result["technique"] = None
            result["confidence"] = 0
            result["explanation"] = ""
        return result
    except Exception as e:
        logger.warning(f"Groq classification error: {e}")
        return {"technique": None, "confidence": 0, "explanation": ""}


# ---------------------------------------------------------------------------
# Span mapping
# ---------------------------------------------------------------------------

def find_span(original_text: str, sentence: str) -> tuple[int, int]:
    """Find the character start/end offset of sentence in original_text."""
    # Try exact match first
    idx = original_text.find(sentence)
    if idx != -1:
        return idx, idx + len(sentence)
    # Fallback: strip and try
    stripped = sentence.strip()
    idx = original_text.find(stripped)
    if idx != -1:
        return idx, idx + len(stripped)
    # Last resort: partial match (first 30 chars)
    partial = stripped[:30] if len(stripped) > 30 else stripped
    idx = original_text.find(partial)
    if idx != -1:
        return idx, idx + len(stripped)
    return (-1, -1)


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def analyze_text(text: str) -> dict:
    """
    Full analysis pipeline.
    Returns structured JSON with spans, techniques, scores, language.
    """
    analysis_id = str(uuid.uuid4())
    start_time = time.time()

    # 1. Language detection
    try:
        lang = detect(text)
    except LangDetectException:
        lang = "en"

    original_text = text
    translated_text = text

    # 2. Translate if Hindi
    if lang == "hi":
        try:
            translated_text = translate_hi_to_en(text)
        except Exception as e:
            logger.warning(f"Translation failed: {e}. Proceeding with original.")
            translated_text = text

    # 3. Sentence tokenize
    sentences = nltk.sent_tokenize(translated_text)
    if not sentences:
        sentences = [translated_text]

    # 4. Classify each sentence
    detected_spans = []
    technique_counts: dict[str, int] = {t: 0 for t in TECHNIQUES}
    technique_confidences: dict[str, list[float]] = {t: [] for t in TECHNIQUES}
    total_confidence = 0.0
    manipulative_count = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        result = classify_sentence(sentence)
        technique = result.get("technique")
        confidence = result.get("confidence", 0)
        explanation = result.get("explanation", "")

        if technique and confidence > 15:
            # Map span back to original text
            # If translated, try to find equivalent in translated first, then map positionally
            search_in = original_text if lang != "hi" else translated_text
            start, end = find_span(search_in, sentence)

            detected_spans.append({
                "technique": technique,
                "confidence": confidence,
                "explanation": explanation,
                "text": sentence,
                "start": start,
                "end": end,
                "color": TECHNIQUE_COLORS.get(technique, "#9CA3AF"),
            })

            technique_counts[technique] += 1
            technique_confidences[technique].append(confidence)
            total_confidence += confidence
            manipulative_count += 1

    # 5. Score aggregation
    total_sentences = max(len(sentences), 1)
    manipulation_ratio = manipulative_count / total_sentences

    # Weighted score: ratio × avg confidence
    if manipulative_count > 0:
        avg_confidence = total_confidence / manipulative_count
        raw_score = manipulation_ratio * avg_confidence
        # Scale to 0-100
        overall_score = min(100, int(raw_score * 1.4))
    else:
        overall_score = 0

    # 6. Credibility rating
    credibility = "Trustworthy"
    for rating, (low, high) in CREDIBILITY_THRESHOLDS.items():
        if low <= overall_score < high:
            credibility = rating
            break

    # 7. Per-technique summary
    technique_breakdown = []
    for technique in TECHNIQUES:
        count = technique_counts[technique]
        avg_conf = (
            sum(technique_confidences[technique]) / len(technique_confidences[technique])
            if technique_confidences[technique]
            else 0
        )
        technique_breakdown.append({
            "technique": technique,
            "count": count,
            "avg_confidence": round(avg_conf, 1),
            "color": TECHNIQUE_COLORS[technique],
        })

    elapsed = round(time.time() - start_time, 2)

    return {
        "analysis_id": analysis_id,
        "language": lang,
        "translated": lang == "hi",
        "original_text": original_text,
        "translated_text": translated_text if lang == "hi" else None,
        "overall_score": overall_score,
        "credibility": credibility,
        "spans": detected_spans,
        "technique_breakdown": technique_breakdown,
        "sentence_count": total_sentences,
        "manipulative_sentence_count": manipulative_count,
        "processing_time_seconds": elapsed,
    }
