"""Claude AI adapter."""
from __future__ import annotations

import asyncio
import json
from typing import Optional

import anthropic
import structlog
from anthropic import AsyncAnthropic

from config import settings

logger = structlog.get_logger()


class ClaudeAdapter:
    """Claude AI adapter for situation analysis."""

    def __init__(self) -> None:
        """Initialize Claude adapter."""
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.temperature = settings.claude_temperature
        self.retry_attempts = settings.claude_retry_attempts

    async def analyze_situation(
        self,
        situation: str,
        child_age: str,
        child_gender: str,
        context: Optional[str] = None,
    ) -> dict:
        """Analyze situation using Claude."""
        prompt = self._build_prompt(situation, child_age, child_gender, context)

        for attempt in range(self.retry_attempts):
            try:
                response = await asyncio.wait_for(
                    self._call_claude(prompt),
                    timeout=settings.claude_timeout,
                )
                return self._parse_response(response)
            except asyncio.TimeoutError:
                logger.warning(
                    "Claude request timeout",
                    attempt=attempt + 1,
                    max_attempts=self.retry_attempts,
                )
                if attempt == self.retry_attempts - 1:
                    raise
            except Exception as e:
                logger.error(
                    "Claude request failed",
                    error=str(e),
                    attempt=attempt + 1,
                    max_attempts=self.retry_attempts,
                )
                if attempt == self.retry_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    def _build_prompt(
        self,
        situation: str,
        child_age: str,
        child_gender: str,
        context: Optional[str] = None,
    ) -> str:
        """Build analysis prompt."""
        gender_pronoun = "он" if child_gender == "male" else "она"
        
        prompt = f"""Ты опытный детский психолог и специалист по развитию детей. Проанализируй следующую ситуацию с ребенком.

Информация о ребенке:
- Возраст: {child_age}
- Пол: {"мальчик" if child_gender == "male" else "девочка"}

Ситуация:
{situation}

{f"Дополнительный контекст: {context}" if context else ""}

Проанализируй эту ситуацию и предоставь ответ в формате JSON со следующей структурой:

{{
    "hidden_meaning": "Что на самом деле происходит с ребенком, какие потребности или эмоции {gender_pronoun} выражает через это поведение",
    "immediate_actions": [
        "Конкретное действие 1, которое родитель может предпринять прямо сейчас",
        "Конкретное действие 2",
        "Конкретное действие 3"
    ],
    "long_term_recommendations": [
        "Долгосрочная рекомендация 1 для развития ребенка",
        "Долгосрочная рекомендация 2",
        "Долгосрочная рекомендация 3"
    ],
    "what_not_to_do": [
        "Чего НЕ следует делать в этой ситуации 1",
        "Чего НЕ следует делать 2"
    ],
    "emotional_tone": "positive|neutral|concerning|urgent",
    "confidence_score": 0.85
}}

Важно:
1. Учитывай возрастные особенности ребенка
2. Давай практичные и конкретные советы
3. Будь эмпатичен к родителю
4. emotional_tone определяй по серьезности ситуации:
   - positive: ситуация позитивная или нормальная для развития
   - neutral: обычная ситуация без особых проблем
   - concerning: требует внимания, но не критично
   - urgent: требует немедленного вмешательства
5. confidence_score - уверенность в анализе от 0 до 1

Отвечай ТОЛЬКО валидным JSON без дополнительного текста."""

        return prompt

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API."""
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        
        return message.content[0].text if message.content else ""

    def _parse_response(self, response: str) -> dict:
        """Parse Claude response."""
        try:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
                
            json_str = response[start_idx:end_idx]
            result = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                "hidden_meaning",
                "immediate_actions",
                "long_term_recommendations",
                "what_not_to_do",
                "emotional_tone",
            ]
            
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set defaults if missing
            if "confidence_score" not in result:
                result["confidence_score"] = 0.8
                
            # Validate emotional_tone
            valid_tones = ["positive", "neutral", "concerning", "urgent"]
            if result["emotional_tone"] not in valid_tones:
                result["emotional_tone"] = "neutral"
                
            return result
            
        except Exception as e:
            logger.error("Failed to parse Claude response", error=str(e), response=response[:500])
            
            # Return default response on parse error
            return {
                "hidden_meaning": "Ребенок выражает свои эмоции и потребности через поведение. Важно понять, что стоит за этим поведением.",
                "immediate_actions": [
                    "Спокойно поговорите с ребенком о его чувствах",
                    "Проявите эмпатию и понимание",
                    "Установите четкие, но добрые границы",
                ],
                "long_term_recommendations": [
                    "Развивайте эмоциональный интеллект ребенка",
                    "Создайте безопасную среду для выражения чувств",
                    "Будьте последовательны в своих реакциях",
                ],
                "what_not_to_do": [
                    "Не игнорируйте чувства ребенка",
                    "Не применяйте физические наказания",
                ],
                "emotional_tone": "neutral",
                "confidence_score": 0.5,
            }