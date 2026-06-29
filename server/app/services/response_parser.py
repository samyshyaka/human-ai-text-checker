import json
import re
from typing import Any, Dict, Optional, Tuple


def extract_content_from_api_response(result: Dict[str, Any]) -> Optional[Any]:
    """Extract message content from various Llama/OpenAI response formats."""
    if "completion_message" in result:
        completion_msg = result["completion_message"]
        if isinstance(completion_msg, dict) and "content" in completion_msg:
            if isinstance(completion_msg["content"], dict) and "text" in completion_msg["content"]:
                return completion_msg["content"]["text"]
            return completion_msg["content"]
        return completion_msg

    if "choices" in result and len(result["choices"]) > 0:
        choice = result["choices"][0]
        if "message" in choice:
            return choice["message"]["content"]
        if "text" in choice:
            return choice["text"]

    if "content" in result:
        return result["content"]
    if "text" in result:
        return result["text"]
    if "response" in result:
        return result["response"]

    return None


def _clean_json_content(content: str) -> str:
    content_clean = content.strip()
    if content_clean.startswith("```json") and content_clean.endswith("```"):
        content_clean = re.sub(r"^```json\s*\n?", "", content_clean)
        content_clean = re.sub(r"\n?```$", "", content_clean)
    elif content_clean.startswith("```") and content_clean.endswith("```"):
        content_clean = re.sub(r"^```[a-zA-Z]*\s*\n?", "", content_clean)
        content_clean = re.sub(r"\n?```$", "", content_clean)
    return content_clean.strip()


def _normalize_probabilities(analysis: Dict[str, Any]) -> Tuple[float, float]:
    ai_prob = float(analysis.get("ai_probability", 0.5))
    human_prob = float(analysis.get("human_probability", 0.5))

    if "ai_probability" in analysis and "human_probability" in analysis:
        return ai_prob, human_prob
    if "ai_probability" in analysis:
        return ai_prob, 1.0 - ai_prob
    if "human_probability" in analysis:
        return 1.0 - human_prob, human_prob
    return 0.5, 0.5


def _parse_analysis_dict(content: Any) -> Dict[str, Any]:
    if isinstance(content, dict):
        analysis = content
    elif isinstance(content, str):
        analysis = json.loads(_clean_json_content(content))
    else:
        analysis = json.loads(str(content))

    ai_prob, human_prob = _normalize_probabilities(analysis)
    return {
        "ai_probability": ai_prob,
        "human_probability": human_prob,
        "reasoning": analysis.get("reasoning", "Analysis completed"),
        "llama_analysis": analysis,
    }


def _fallback_text_analysis(content: Any) -> Dict[str, Any]:
    content_str = str(content)
    ai_prob = 0.5
    human_prob = 0.5

    ai_match = re.search(r'"ai_probability":\s*(\d+(?:\.\d+)?)', content_str)
    human_match = re.search(r'"human_probability":\s*(\d+(?:\.\d+)?)', content_str)
    ai_match_no_quotes = re.search(r"ai_probability:\s*(\d+(?:\.\d+)?)", content_str, re.IGNORECASE)
    human_match_no_quotes = re.search(
        r"human_probability:\s*(\d+(?:\.\d+)?)", content_str, re.IGNORECASE
    )

    if ai_match and human_match:
        ai_prob = float(ai_match.group(1))
        human_prob = float(human_match.group(1))
    elif ai_match_no_quotes and human_match_no_quotes:
        ai_prob = float(ai_match_no_quotes.group(1))
        human_prob = float(human_match_no_quotes.group(1))
    elif ai_match or ai_match_no_quotes:
        match = ai_match if ai_match else ai_match_no_quotes
        ai_prob = float(match.group(1))
        human_prob = 1.0 - ai_prob
    elif human_match or human_match_no_quotes:
        match = human_match if human_match else human_match_no_quotes
        human_prob = float(match.group(1))
        ai_prob = 1.0 - human_prob
    else:
        prob_pattern = r"\b(?:ai|human)?\s*probability\s*[=:]\s*(\d+(?:\.\d+)?)"
        prob_matches = re.findall(prob_pattern, content_str, re.IGNORECASE)
        if prob_matches:
            first_prob = float(prob_matches[0])
            if 0 <= first_prob <= 1:
                ai_prob = first_prob
                human_prob = 1.0 - first_prob
        else:
            decimal_matches = re.findall(r"\b0\.\d+\b", content_str)
            if len(decimal_matches) >= 2:
                ai_prob = float(decimal_matches[0])
                human_prob = float(decimal_matches[1])
            elif len(decimal_matches) == 1:
                ai_prob = float(decimal_matches[0])
                human_prob = 1.0 - ai_prob

    return {
        "ai_probability": ai_prob,
        "human_probability": human_prob,
        "reasoning": (
            f"Text analysis fallback - JSON parsing failed. "
            f"Extracted probabilities from text: AI={ai_prob}, Human={human_prob}"
        ),
        "fallback_method": "text_analysis",
        "note": "This is a fallback response. Check server logs to see why JSON parsing failed.",
        "source": "fallback_text_analysis",
        "extraction_method": "fallback",
    }


def parse_llama_analysis(content: Any, raw_api_response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Llama response content into normalized analysis fields."""
    try:
        parsed = _parse_analysis_dict(content)
        return {
            **parsed,
            "raw_response": content,
            "debug_api_response": raw_api_response,
            "source": "llama_json_parsing",
            "extraction_method": "json_success",
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        fallback = _fallback_text_analysis(content)
        return {
            **fallback,
            "raw_response": content,
            "debug_api_response": raw_api_response,
        }
