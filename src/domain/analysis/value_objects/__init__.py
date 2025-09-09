"""Value objects for Analysis bounded context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SituationDescription:
    """Situation description value object."""
    
    value: str
    
    def __post_init__(self) -> None:
        if not self.value or len(self.value.strip()) < 10:
            raise ValueError("Situation description must be at least 10 characters")
        if len(self.value) > 2000:
            raise ValueError("Situation description is too long (max 2000 characters)")
    
    def __str__(self) -> str:
        return self.value