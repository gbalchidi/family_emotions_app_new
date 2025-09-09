"""Claude API analyzer service."""

import json
from typing import Dict, Any

from anthropic import AsyncAnthropic

from src.domain.analysis.aggregates import AIRecommendation
from src.infrastructure.config.settings import settings


class ClaudeAnalyzer:
    """Claude API analyzer implementation."""
    
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model
    
    async def analyze_situation(
        self,
        situation: str,
        child_age: int,
        child_gender: str
    ) -> AIRecommendation:
        """Analyze situation using Claude API."""
        prompt = self._build_prompt(situation, child_age, child_gender)
        
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            content = response.content[0].text
            analysis = self._parse_response(content)
            
            return AIRecommendation(
                hidden_meaning=analysis["hidden_meaning"],
                immediate_actions=analysis["immediate_actions"],
                long_term_recommendations=analysis["long_term_recommendations"],
                what_not_to_do=analysis["what_not_to_do"],
                confidence_score=analysis.get("confidence_score", 0.8)
            )
            
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}")
    
    def _build_prompt(self, situation: str, child_age: int, child_gender: str) -> str:
        """Build analysis prompt."""
        gender_pronoun = "он" if child_gender == "male" else "она" if child_gender == "female" else "ребенок"
        
        return f"""Ты опытный детский психолог и эксперт по воспитанию детей. 
Родитель обратился к тебе за помощью в понимании поведения ребенка.

Информация о ребенке:
- Возраст: {child_age} лет
- Пол: {child_gender}

Ситуация, описанная родителем:
"{situation}"

Проанализируй ситуацию и предоставь ответ в формате JSON со следующими полями:

{{
    "hidden_meaning": "Глубинный анализ: что на самом деле может чувствовать или хотеть выразить ребенок через это поведение/слова",
    "immediate_actions": "Что делать прямо сейчас: конкретные действия, которые родитель может предпринять немедленно",
    "long_term_recommendations": "Долгосрочные рекомендации: стратегии воспитания и развития отношений с ребенком",
    "what_not_to_do": "Чего НЕ следует делать: распространенные ошибки, которых нужно избегать в данной ситуации",
    "confidence_score": 0.85
}}

Важно:
1. Учитывай возраст ребенка при анализе
2. Давай практичные и выполнимые советы
3. Будь эмпатичным к родителю
4. Избегай осуждения
5. Фокусируйся на развитии здоровых отношений между родителем и ребенком

Ответь только JSON без дополнительного текста."""
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse Claude response."""
        try:
            # Try to extract JSON from response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            
            # Fallback parsing if JSON extraction fails
            return {
                "hidden_meaning": "Требуется дополнительный анализ ситуации",
                "immediate_actions": content[:500] if len(content) > 500 else content,
                "long_term_recommendations": "Обратите внимание на эмоциональное состояние ребенка",
                "what_not_to_do": "Избегайте резких реакций",
                "confidence_score": 0.5
            }
            
        except json.JSONDecodeError:
            # Return default structure if parsing fails
            return {
                "hidden_meaning": "Анализ ситуации требует внимания",
                "immediate_actions": "Сохраняйте спокойствие и выслушайте ребенка",
                "long_term_recommendations": "Работайте над укреплением доверия",
                "what_not_to_do": "Не игнорируйте чувства ребенка",
                "confidence_score": 0.6
            }