from abc import ABC, abstractmethod


class SMSSender(ABC):
    @abstractmethod
    def send(self, numbers: list[str], message: str) -> None:
        """Send an SMS to the given numbers with the given message."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the sender backend is available and ready."""
        ...


class PhoneLinkSender(SMSSender):
    def __init__(self, on_log=None):
        from automation.phone_link import PhoneLinkSender as _PhoneLinkAutomation
        self._automation = _PhoneLinkAutomation(on_log=on_log)

    def send(self, numbers: list[str], message: str) -> None:
        self._automation.send_batch(numbers, message)

    def is_available(self) -> bool:
        return self._automation.is_available()
