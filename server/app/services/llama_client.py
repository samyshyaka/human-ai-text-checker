from typing import Dict, Optional

import aiohttp
from fastapi import HTTPException

import config
from app.services.response_parser import extract_content_from_api_response, parse_llama_analysis


class LlamaAPIClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or config.LLAMA_API_KEY
        self.api_url = api_url or config.LLAMA_API_URL
        self.model = model or config.LLAMA_MODEL

        if not self.api_key:
            raise ValueError("No API key found. Please set LLAMA_API_KEY environment variable.")

    async def analyze_text_with_llama(self, text: str, context: str) -> Dict:
        prompt = f"""Context: {context}

Analyze the following text and determine the probability that it was written by AI versus a human.

Consider factors like:
- Writing patterns and consistency across paragraphs
- Vocabulary usage and complexity
- Sentence structure and flow
- Creative elements and personal touches
- Error patterns typical of AI or human writing
- Paragraph transitions and coherence
- Personal anecdotes or experiences
- Emotional authenticity

Text to analyze:
---
{text}
---

Respond with a JSON object containing:
- ai_probability: float between 0 and 1
- human_probability: float between 0 and 1
- reasoning: brief explanation of your analysis

Format your response as valid JSON only."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert AI detector that can analyze text and determine "
                        "if it was written by AI or humans. Always respond with valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.3,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Llama API error: {error_text}",
                        )

                    result = await response.json()
                    content = extract_content_from_api_response(result)

                    if not content:
                        raise HTTPException(
                            status_code=500,
                            detail=(
                                "Could not extract content from API response. "
                                f"Response keys: {list(result.keys())}"
                            ),
                        )

                    return parse_llama_analysis(content, result)

        except aiohttp.ClientError as exc:
            raise HTTPException(status_code=500, detail=f"Network error: {str(exc)}") from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}") from exc

    async def humanize_text(
        self,
        text: str,
        human_examples: str = "",
        refinement_note: str = "",
        attempt: int = 1,
    ) -> Dict:
        examples_block = ""
        if human_examples:
            examples_block = f"""Study how real humans write in these examples — match their rhythm, not their topic:
---
{human_examples}
---

"""

        refinement_block = f"\nIMPORTANT — previous attempt failed verification:\n{refinement_note}\n" if refinement_note else ""

        intensity_guide = {
            1: """Rewrite level: natural human.
- Vary sentence length (mix short and long)
- Use contractions where they fit (don't, it's, I've)
- Remove AI filler: "Furthermore", "Moreover", "In conclusion", "It is important to note", "This demonstrates"
- Prefer concrete wording over abstract summary language""",
            2: """Rewrite level: more informal and uneven.
- Break up any remaining polished or essay-like flow
- Use a conversational tone — like explaining the idea to someone, not writing a report
- Allow occasional sentence fragments or starting with "And" or "But"
- Avoid symmetrical paragraph structure and parallel bullet-style phrasing
- Sound slightly rougher, not smarter""",
            3: """Rewrite level: distinctly human, imperfect on purpose.
- Write like a draft a person would actually submit — not a cleaned-up AI revision
- Mix very short sentences with longer ones; do not maintain consistent formality
- Drop corporate/academic tone entirely
- Use plain words instead of elevated vocabulary
- Let transitions be loose; do not summarize at the end
- If it reads too smooth or too balanced, make it messier while keeping the facts""",
        }
        intensity = intensity_guide.get(attempt, intensity_guide[3])

        prompt = f"""{examples_block}{refinement_block}Rewrite the text below so an AI detector would classify it as human-written.

{intensity}

Rules:
- Keep the same facts and main points — do not invent experiences or false claims
- Do not mention AI, rewriting, or detection
- Return ONLY the rewritten text — no labels, quotes, or explanation

Original text:
---
{text}
---"""

        temperature = {1: 0.78, 2: 0.88, 3: 0.95}.get(attempt, 0.95)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You rewrite text to sound like a real human wrote it in one sitting — "
                        "informal, uneven, and authentic. Never sound like ChatGPT or a textbook. "
                        "Preserve meaning; change voice and rhythm."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1500,
            "temperature": temperature,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Llama API error: {error_text}",
                        )

                    result = await response.json()
                    content = extract_content_from_api_response(result)

                    if not content:
                        raise HTTPException(
                            status_code=500,
                            detail=(
                                "Could not extract humanized text from API response. "
                                f"Response keys: {list(result.keys())}"
                            ),
                        )

                    humanized = str(content).strip()
                    return {
                        "humanized_text": humanized,
                        "status": "success",
                    }

        except aiohttp.ClientError as exc:
            raise HTTPException(status_code=500, detail=f"Network error: {str(exc)}") from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}") from exc

    async def test_simple_request(self) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "Say hello"}],
            "max_tokens": 20,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                status = response.status
                if status == 200:
                    response_json = await response.json()
                    return {
                        "status_code": status,
                        "success": True,
                        "full_response": response_json,
                        "response_keys": list(response_json.keys()),
                        "api_url": self.api_url,
                        "model": self.model,
                    }

                response_text = await response.text()
                return {
                    "status_code": status,
                    "success": False,
                    "error_response": response_text,
                    "api_url": self.api_url,
                    "model": self.model,
                }
