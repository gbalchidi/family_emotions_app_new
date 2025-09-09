"""Integration tests for Claude adapter."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from anthropic import AsyncAnthropic

from infrastructure.claude.adapter import ClaudeAdapter


class TestClaudeAdapterIntegration:
    """Claude adapter integration tests."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.adapter = None  # Will be created in tests to avoid API calls

    @patch("infrastructure.claude.adapter.settings")
    def test_adapter_initialization(self, mock_settings) -> None:
        """Test Claude adapter initialization."""
        # Mock settings
        mock_settings.anthropic_api_key = "test-api-key"
        mock_settings.claude_model = "claude-3-sonnet-20240229"
        mock_settings.claude_max_tokens = 2000
        mock_settings.claude_temperature = 0.7
        mock_settings.claude_retry_attempts = 3
        mock_settings.claude_timeout = 30

        adapter = ClaudeAdapter()

        assert adapter.model == "claude-3-sonnet-20240229"
        assert adapter.max_tokens == 2000
        assert adapter.temperature == 0.7
        assert adapter.retry_attempts == 3
        assert isinstance(adapter.client, AsyncAnthropic)

    async def test_build_prompt_with_all_parameters(self) -> None:
        """Test building prompt with all parameters."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-sonnet-20240229"
            mock_settings.claude_max_tokens = 2000
            mock_settings.claude_temperature = 0.7
            mock_settings.claude_retry_attempts = 3

            adapter = ClaudeAdapter()

            prompt = adapter._build_prompt(
                situation="Ребенок не хочет идти в школу",
                child_age="7 лет",
                child_gender="male",
                context="Это началось на этой неделе",
            )

            # Check that all parameters are included in prompt
            assert "Ребенок не хочет идти в школу" in prompt
            assert "7 лет" in prompt
            assert "мальчик" in prompt
            assert "Это началось на этой неделе" in prompt
            assert "он" in prompt  # Male pronoun
            assert "JSON" in prompt
            assert "emotional_tone" in prompt

    async def test_build_prompt_without_context(self) -> None:
        """Test building prompt without context."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-sonnet-20240229"
            mock_settings.claude_max_tokens = 2000
            mock_settings.claude_temperature = 0.7
            mock_settings.claude_retry_attempts = 3

            adapter = ClaudeAdapter()

            prompt = adapter._build_prompt(
                situation="Ребенок капризничает",
                child_age="5 лет",
                child_gender="female",
                context=None,
            )

            assert "Ребенок капризничает" in prompt
            assert "5 лет" in prompt
            assert "девочка" in prompt
            assert "она" in prompt  # Female pronoun
            assert "Дополнительный контекст:" not in prompt

    async def test_parse_valid_response(self) -> None:
        """Test parsing valid Claude response."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            adapter = ClaudeAdapter()

            valid_response = """Here is the analysis:

{
    "hidden_meaning": "Ребенок испытывает стресс",
    "immediate_actions": [
        "Поговорить с ребенком",
        "Обнять ребенка"
    ],
    "long_term_recommendations": [
        "Создать режим",
        "Больше времени проводить вместе"
    ],
    "what_not_to_do": [
        "Не кричать",
        "Не наказывать"
    ],
    "emotional_tone": "concerning",
    "confidence_score": 0.85
}

That's my analysis."""

            result = adapter._parse_response(valid_response)

            assert result["hidden_meaning"] == "Ребенок испытывает стресс"
            assert len(result["immediate_actions"]) == 2
            assert len(result["long_term_recommendations"]) == 2
            assert len(result["what_not_to_do"]) == 2
            assert result["emotional_tone"] == "concerning"
            assert result["confidence_score"] == 0.85

    async def test_parse_response_without_confidence_score(self) -> None:
        """Test parsing response without confidence score (should add default)."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            adapter = ClaudeAdapter()

            response_without_confidence = """{
    "hidden_meaning": "Ребенок устал",
    "immediate_actions": ["Дать отдохнуть"],
    "long_term_recommendations": ["Режим сна"],
    "what_not_to_do": ["Не заставлять"],
    "emotional_tone": "neutral"
}"""

            result = adapter._parse_response(response_without_confidence)

            assert result["confidence_score"] == 0.8  # Default value

    async def test_parse_response_invalid_emotional_tone(self) -> None:
        """Test parsing response with invalid emotional tone (should fix to neutral)."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            adapter = ClaudeAdapter()

            response_invalid_tone = """{
    "hidden_meaning": "Ребенок устал",
    "immediate_actions": ["Дать отдохнуть"],
    "long_term_recommendations": ["Режим сна"],
    "what_not_to_do": ["Не заставлять"],
    "emotional_tone": "invalid_tone",
    "confidence_score": 0.9
}"""

            result = adapter._parse_response(response_invalid_tone)

            assert result["emotional_tone"] == "neutral"  # Fixed value

    async def test_parse_invalid_json_response(self) -> None:
        """Test parsing invalid JSON response (should return default)."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            adapter = ClaudeAdapter()

            invalid_response = "This is not a JSON response at all"

            result = adapter._parse_response(invalid_response)

            # Should return default response
            assert "hidden_meaning" in result
            assert "immediate_actions" in result
            assert "long_term_recommendations" in result
            assert "what_not_to_do" in result
            assert result["emotional_tone"] == "neutral"
            assert result["confidence_score"] == 0.5

    async def test_parse_incomplete_json_response(self) -> None:
        """Test parsing JSON response missing required fields."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            adapter = ClaudeAdapter()

            incomplete_response = """{
    "hidden_meaning": "Ребенок устал",
    "immediate_actions": ["Дать отдохнуть"]
}"""

            result = adapter._parse_response(incomplete_response)

            # Should return default response
            assert result["emotional_tone"] == "neutral"
            assert result["confidence_score"] == 0.5

    async def test_analyze_situation_success(self) -> None:
        """Test successful situation analysis with mocked Claude API."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-sonnet-20240229"
            mock_settings.claude_max_tokens = 2000
            mock_settings.claude_temperature = 0.7
            mock_settings.claude_retry_attempts = 3
            mock_settings.claude_timeout = 30

            adapter = ClaudeAdapter()

            # Mock the Claude API call
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = """{
    "hidden_meaning": "Ребенок испытывает страх перед школой",
    "immediate_actions": [
        "Поговорить с ребенком о его переживаниях",
        "Выяснить причину страха"
    ],
    "long_term_recommendations": [
        "Постепенно адаптировать к школьной среде",
        "Развивать социальные навыки"
    ],
    "what_not_to_do": [
        "Не заставлять идти силой",
        "Не игнорировать страхи"
    ],
    "emotional_tone": "concerning",
    "confidence_score": 0.9
}"""

            with patch.object(adapter.client.messages, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_response

                result = await adapter.analyze_situation(
                    situation="Ребенок не хочет идти в школу и плачет каждое утро",
                    child_age="6 лет",
                    child_gender="female",
                    context="Начался новый учебный год",
                )

                # Verify API was called
                mock_create.assert_called_once()
                call_args = mock_create.call_args
                assert call_args[1]["model"] == "claude-3-sonnet-20240229"
                assert call_args[1]["max_tokens"] == 2000
                assert call_args[1]["temperature"] == 0.7

                # Verify response parsing
                assert result["hidden_meaning"] == "Ребенок испытывает страх перед школой"
                assert len(result["immediate_actions"]) == 2
                assert result["emotional_tone"] == "concerning"
                assert result["confidence_score"] == 0.9

    async def test_analyze_situation_with_retry_on_timeout(self) -> None:
        """Test situation analysis with retry on timeout."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-sonnet-20240229"
            mock_settings.claude_max_tokens = 2000
            mock_settings.claude_temperature = 0.7
            mock_settings.claude_retry_attempts = 3
            mock_settings.claude_timeout = 0.001  # Very short timeout

            adapter = ClaudeAdapter()

            # Mock Claude API to be slow (causing timeout)
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = '{"hidden_meaning": "test"}'

            with patch.object(adapter.client.messages, 'create', new_callable=AsyncMock) as mock_create:
                # First call times out, second succeeds
                async def slow_then_fast(*args, **kwargs):
                    if mock_create.call_count == 1:
                        await asyncio.sleep(0.1)  # This will timeout
                    return mock_response

                mock_create.side_effect = slow_then_fast

                with pytest.raises(asyncio.TimeoutError):
                    await adapter.analyze_situation(
                        situation="Test situation",
                        child_age="5 лет",
                        child_gender="male",
                    )

                # Should have been called the maximum number of times
                assert mock_create.call_count == 3

    async def test_analyze_situation_with_retry_on_exception(self) -> None:
        """Test situation analysis with retry on API exception."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-3-sonnet-20240229"
            mock_settings.claude_retry_attempts = 2
            mock_settings.claude_timeout = 30

            adapter = ClaudeAdapter()

            # Mock the sleep to speed up tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with patch.object(adapter.client.messages, 'create', new_callable=AsyncMock) as mock_create:
                    # First call fails, second succeeds
                    mock_response = Mock()
                    mock_response.content = [Mock()]
                    mock_response.content[0].text = """{
    "hidden_meaning": "Success on retry",
    "immediate_actions": ["Action"],
    "long_term_recommendations": ["Rec"],
    "what_not_to_do": ["Don't"],
    "emotional_tone": "neutral"
}"""

                    mock_create.side_effect = [
                        Exception("API error"),
                        mock_response,
                    ]

                    result = await adapter.analyze_situation(
                        situation="Test situation",
                        child_age="5 лет",
                        child_gender="male",
                    )

                    # Should have retried once
                    assert mock_create.call_count == 2
                    assert result["hidden_meaning"] == "Success on retry"

    async def test_analyze_situation_all_retries_fail(self) -> None:
        """Test situation analysis when all retries fail."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_retry_attempts = 2
            mock_settings.claude_timeout = 30

            adapter = ClaudeAdapter()

            # Mock the sleep to speed up tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with patch.object(adapter.client.messages, 'create', new_callable=AsyncMock) as mock_create:
                    # All calls fail
                    mock_create.side_effect = Exception("Persistent API error")

                    with pytest.raises(Exception, match="Persistent API error"):
                        await adapter.analyze_situation(
                            situation="Test situation",
                            child_age="5 лет",
                            child_gender="male",
                        )

                    # Should have tried the maximum number of times
                    assert mock_create.call_count == 2

    @pytest.mark.parametrize(
        "gender,expected_pronoun,expected_gender_word",
        [
            ("male", "он", "мальчик"),
            ("female", "она", "девочка"),
            ("other", "она", "девочка"),  # Default to female
        ],
    )
    async def test_build_prompt_gender_handling(
        self, gender: str, expected_pronoun: str, expected_gender_word: str
    ) -> None:
        """Test that prompt builder handles different genders correctly."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            adapter = ClaudeAdapter()

            prompt = adapter._build_prompt(
                situation="Test situation",
                child_age="5 лет",
                child_gender=gender,
            )

            assert expected_pronoun in prompt
            assert expected_gender_word in prompt

    async def test_empty_claude_response(self) -> None:
        """Test handling of empty Claude response."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_timeout = 30
            mock_settings.claude_retry_attempts = 1

            adapter = ClaudeAdapter()

            # Mock empty response
            mock_response = Mock()
            mock_response.content = []

            with patch.object(adapter.client.messages, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_response

                result = await adapter.analyze_situation(
                    situation="Test situation",
                    child_age="5 лет",
                    child_gender="male",
                )

                # Should return default response
                assert result["emotional_tone"] == "neutral"
                assert result["confidence_score"] == 0.5

    async def test_malformed_json_in_response(self) -> None:
        """Test handling of malformed JSON in Claude response."""
        with patch("infrastructure.claude.adapter.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            adapter = ClaudeAdapter()

            malformed_responses = [
                '{"hidden_meaning": "test", "immediate_actions": [',  # Incomplete JSON
                '{"hidden_meaning": "test" "immediate_actions": []}',  # Missing comma
                'Not JSON at all {invalid}',
                '',  # Empty string
            ]

            for malformed_response in malformed_responses:
                result = adapter._parse_response(malformed_response)
                
                # Should return default response for all malformed inputs
                assert result["emotional_tone"] == "neutral"
                assert result["confidence_score"] == 0.5
                assert "immediate_actions" in result
                assert isinstance(result["immediate_actions"], list)