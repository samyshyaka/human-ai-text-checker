from typing import Dict, Optional

from fastapi import HTTPException

import config
from app.rag.vectorstore import RAGService
from app.services.analysis import is_classified_as_human, run_llama_analysis
from app.services.llama_client import LlamaAPIClient


async def run_humanize(
    text: str,
    llama_client: Optional[LlamaAPIClient],
    rag_service: RAGService,
) -> Dict:
    if llama_client is None:
        raise HTTPException(
            status_code=503,
            detail="Llama API not configured. Set LLAMA_API_KEY to use humanization.",
        )

    last_verification: Optional[Dict] = None
    humanized_text = text

    for attempt in range(1, config.HUMANIZE_MAX_ATTEMPTS + 1):
        human_examples = rag_service.retrieve_human_examples(humanized_text)
        refinement_note = ""
        if attempt > 1 and last_verification:
            ai_pct = round(float(last_verification["ai_probability"]) * 100)
            human_pct = round(float(last_verification["human_probability"]) * 100)
            if attempt == 2:
                refinement_note = (
                    f"Attempt {attempt - 1} still scored AI {ai_pct}% / Human {human_pct}%. "
                    "The rewrite was too polished and essay-like. "
                    "Make it sound like casual speech — uneven sentences, plain words, "
                    "no formal transitions, no summary closing."
                )
            else:
                refinement_note = (
                    f"Attempts 1–{attempt - 1} still scored as AI (last: AI {ai_pct}%, Human {human_pct}%). "
                    "Go much further: write like a rough first draft by a real person. "
                    "Allow fragments, informal openers, inconsistent rhythm, and simpler vocabulary. "
                    "It should NOT read like a revised AI paragraph."
                )

        rewrite_result = await llama_client.humanize_text(
            text,
            human_examples,
            refinement_note=refinement_note,
            attempt=attempt,
        )
        humanized_text = rewrite_result["humanized_text"]

        last_verification = await run_llama_analysis(
            humanized_text, llama_client, rag_service
        )

        if is_classified_as_human(last_verification):
            return {
                "humanized_text": humanized_text,
                "original_text": text,
                "status": "verified_human",
                "verification": {
                    "human_probability": last_verification["human_probability"],
                    "ai_probability": last_verification["ai_probability"],
                    "reasoning": last_verification.get("reasoning"),
                    "attempts": attempt,
                },
            }

    ai_pct = round(float(last_verification["ai_probability"]) * 100)
    human_pct = round(float(last_verification["human_probability"]) * 100)
    raise HTTPException(
        status_code=422,
        detail=(
            f"Could not produce human-classified text after "
            f"{config.HUMANIZE_MAX_ATTEMPTS} attempts. "
            f"Last scores: AI {ai_pct}%, Human {human_pct}%."
        ),
    )
