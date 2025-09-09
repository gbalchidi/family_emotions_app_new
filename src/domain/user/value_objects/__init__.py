"""Value objects for User bounded context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramId:
    """Telegram user ID value object."""
    
    value: int
    
    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("Telegram ID must be positive")
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class UserName:
    """User name value object."""
    
    value: str
    
    def __post_init__(self) -> None:
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Name cannot be empty")
        if len(self.value) > 100:
            raise ValueError("Name is too long (max 100 characters)")
    
    def __str__(self) -> str:
        return self.value