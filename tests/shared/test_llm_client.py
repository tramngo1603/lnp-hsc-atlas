"""Tests for shared.llm_client — unified LLM abstraction."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from shared.llm_client import extract_structured_data


class SampleOutput(BaseModel):
    """Test model for extraction."""

    name: str
    value: float


class TestExtractStructuredData:
    """Test the extract_structured_data function."""

    @pytest.fixture(autouse=True)
    def _clear_settings(self) -> None:  # type: ignore[misc]
        from shared.config import get_settings

        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    async def test_parses_valid_json_response(self) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"name": "MC3", "value": 50.5}')]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("shared.llm_client.AsyncAnthropic", return_value=mock_client):
            result = await extract_structured_data(
                system_prompt="Extract lipid data.",
                user_content="The ionizable lipid MC3 was used at 50.5 mol%.",
                response_model=SampleOutput,
            )

        assert isinstance(result, SampleOutput)
        assert result.name == "MC3"
        assert result.value == 50.5

    async def test_strips_markdown_fences(self) -> None:
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text='```json\n{"name": "ALC-0315", "value": 46.3}\n```')
        ]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("shared.llm_client.AsyncAnthropic", return_value=mock_client):
            result = await extract_structured_data(
                system_prompt="Extract.",
                user_content="ALC-0315 at 46.3%.",
                response_model=SampleOutput,
            )

        assert result.name == "ALC-0315"
        assert result.value == 46.3

    async def test_raises_on_invalid_json(self) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="not valid json at all")]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with (
            patch("shared.llm_client.AsyncAnthropic", return_value=mock_client),
            pytest.raises(ValueError, match="Failed to parse"),
        ):
            await extract_structured_data(
                system_prompt="Extract.",
                user_content="some text",
                response_model=SampleOutput,
            )

    async def test_sends_correct_system_prompt_with_schema(self) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"name": "test", "value": 1.0}')]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("shared.llm_client.AsyncAnthropic", return_value=mock_client):
            await extract_structured_data(
                system_prompt="You are a scientist.",
                user_content="data",
                response_model=SampleOutput,
            )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "You are a scientist." in call_kwargs["system"]
        assert "name" in call_kwargs["system"]  # schema included
        assert call_kwargs["messages"][0]["content"] == "data"
