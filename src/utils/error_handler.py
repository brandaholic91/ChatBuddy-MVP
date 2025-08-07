# src/utils/error_handler.py

from typing import Dict, Any
from src.config.messages import ERROR_MESSAGES

class ChatBuddyError(Exception):
    """Custom exception for ChatBuddy application errors."""
    def __init__(self, error_key: str, lang: str = "HU", **kwargs: Any) -> None:
        self.error_key = error_key
        self.lang = lang
        self.details = ERROR_MESSAGES.get(lang, {}).get(error_key, {})
        self.code = self.details.get("code", "UNKNOWN")
        self.message = self.details.get("message", "Ismeretlen hiba történt.").format(**kwargs)
        self.action = self.details.get("action", "Kérjük, próbálja újra később.").format(**kwargs)
        self.category = self.details.get("category", "General")
        super().__init__(f"[{self.code}] {self.message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "action": self.action,
            "category": self.category,
            "error_key": self.error_key,
            "lang": self.lang
        }

def get_error_message(error_key: str, lang: str = "HU", **kwargs: Any) -> Dict[str, Any]:
    """Retrieves a formatted error message based on error_key and language."""
    error_info = ERROR_MESSAGES.get(lang, {}).get(error_key, {})
    return {
        "code": error_info.get("code", "UNKNOWN"),
        "message": error_info.get("message", "Ismeretlen hiba történt.").format(**kwargs),
        "action": error_info.get("action", "Kérjük, próbálja újra később.").format(**kwargs),
        "category": error_info.get("category", "General")
    }