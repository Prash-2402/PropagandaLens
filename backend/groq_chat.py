"""
groq_chat.py — Chat handler for PropagandaLens.

Maintains conversational context about the analyzed text,
supporting questions like:
  - "Why is this propaganda?"
  - "Which sentence is most dangerous?"
  - "Rewrite this neutrally"
"""

import os
import json
import logging
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"

_groq_client: Optional[Groq] = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def build_system_prompt(analysis_context: dict) -> str:
    """Build a rich system prompt embedding analysis results as context."""
    original_text = analysis_context.get("original_text", "")
    overall_score = analysis_context.get("overall_score", 0)
    credibility = analysis_context.get("credibility", "Unknown")
    language = analysis_context.get("language", "en")
    spans = analysis_context.get("spans", [])

    # Summarize detected spans
    span_summaries = []
    for i, span in enumerate(spans, 1):
        span_summaries.append(
            f'{i}. [{span["technique"]} | {span["confidence"]}% confidence] '
            f'"{span["text"]}" — {span["explanation"]}'
        )
    spans_text = "\n".join(span_summaries) if span_summaries else "No manipulation detected."

    return f"""You are PropagandaLens AI — an expert in propaganda analysis, rhetoric, and media literacy.

You have already analyzed the following text using advanced NLP techniques:

=== ANALYZED TEXT ===
{original_text[:3000]}{"..." if len(original_text) > 3000 else ""}

=== ANALYSIS RESULTS ===
Overall Manipulation Score: {overall_score}/100
Credibility Rating: {credibility}
Detected Language: {language.upper()}

Detected Manipulation Techniques:
{spans_text}

=== YOUR ROLE ===
Answer the user's questions about this analysis. You can:
- Explain why specific sentences are propaganda
- Identify the most dangerous or persuasive sentence
- Rewrite manipulative sections neutrally
- Explain each propaganda technique in simple terms
- Give advice on how to critically evaluate this type of content

Be concise, insightful, and educational. Use plain language accessible to non-experts.
If the user asks to rewrite something neutrally, provide a clear before/after comparison.
"""


def chat(
    message: str,
    analysis_context: dict,
    history: list[dict] | None = None,
) -> str:
    """
    Send a chat message with analysis context.
    
    Args:
        message: User's question
        analysis_context: Full analysis JSON from analyzer.analyze_text()
        history: List of previous {role, content} messages for multi-turn
    
    Returns:
        Assistant's response string
    """
    client = _get_groq_client()

    system_prompt = build_system_prompt(analysis_context)

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (last 10 turns to stay within context)
    if history:
        messages.extend(history[-20:])

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq chat error: {e}")
        raise RuntimeError(f"Chat request failed: {e}")


SUGGESTED_PROMPTS = [
    "Why is this considered propaganda?",
    "Which sentence is most dangerous or manipulative?",
    "Rewrite the most biased sentence neutrally.",
    "What techniques are used most in this text?",
    "How can I recognize these techniques in the future?",
    "Give me a brief summary of what makes this text manipulative.",
]
