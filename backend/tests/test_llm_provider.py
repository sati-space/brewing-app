import pytest

from app.services.llm_provider import LLMProviderError, OpenAICompatibleLLM


def test_parse_suggestions_from_json_content() -> None:
    client = OpenAICompatibleLLM(base_url="https://example.com", api_key=None, model="x")

    content = (
        '{"suggestions": ['
        '{"title": "Tip 1", "rationale": "Why", "action": "Do X", "priority": "high"}, '
        '{"title": "Tip 2", "rationale": "Why 2", "action": "Do Y"}'
        ']}'
    )

    suggestions = client._parse_suggestions(content)  # noqa: SLF001

    assert len(suggestions) == 2
    assert suggestions[0].title == "Tip 1"
    assert suggestions[1].priority == "medium"


def test_parse_suggestions_from_markdown_fence() -> None:
    client = OpenAICompatibleLLM(base_url="https://example.com", api_key=None, model="x")

    content = """
```json
{
  "suggestions": [
    {"title": "Tip 1", "rationale": "Why", "action": "Do X", "priority": "low"}
  ]
}
```
"""

    suggestions = client._parse_suggestions(content)  # noqa: SLF001

    assert len(suggestions) == 1
    assert suggestions[0].title == "Tip 1"


def test_parse_suggestions_raises_for_invalid_json() -> None:
    client = OpenAICompatibleLLM(base_url="https://example.com", api_key=None, model="x")

    with pytest.raises(LLMProviderError):
        client._parse_suggestions("not json")  # noqa: SLF001
