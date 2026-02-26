import json
import re

import httpx

from app.schemas.ai import AISuggestion


class LLMProviderError(RuntimeError):
    """Raised when LLM provider calls fail or return invalid output."""


def _extract_json_block(text: str) -> str:
    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced_match:
        return fenced_match.group(1)

    brace_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if brace_match:
        return brace_match.group(0)

    return text


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, api_key: str | None, model: str, timeout_seconds: int = 20):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _request(self, system_prompt: str, user_prompt: str) -> str:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        url = f"{self.base_url}/v1/chat/completions"

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"LLM request failed: {exc}") from exc

        body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("LLM response missing choices/message content") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("LLM response content is empty")

        return content

    def _parse_suggestions(self, content: str) -> list[AISuggestion]:
        json_text = _extract_json_block(content)
        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("LLM response was not valid JSON") from exc

        suggestions_raw = parsed.get("suggestions") if isinstance(parsed, dict) else None
        if not isinstance(suggestions_raw, list):
            raise LLMProviderError("LLM response missing suggestions list")

        suggestions: list[AISuggestion] = []
        for item in suggestions_raw:
            if not isinstance(item, dict):
                continue
            try:
                suggestions.append(
                    AISuggestion(
                        title=str(item.get("title", "")).strip(),
                        rationale=str(item.get("rationale", "")).strip(),
                        action=str(item.get("action", "")).strip(),
                        priority=str(item.get("priority", "medium")).strip() or "medium",
                    )
                )
            except Exception:
                continue

        suggestions = [s for s in suggestions if s.title and s.rationale and s.action]
        if not suggestions:
            raise LLMProviderError("LLM response did not contain valid suggestions")

        return suggestions

    def suggest(self, *, system_prompt: str, user_prompt: str) -> list[AISuggestion]:
        content = self._request(system_prompt=system_prompt, user_prompt=user_prompt)
        return self._parse_suggestions(content)
