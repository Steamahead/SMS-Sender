from abc import ABC, abstractmethod


class SMSSender(ABC):
    @abstractmethod
    def send(self, numbers: list[str], message: str, on_result=None) -> None:
        """Send an SMS to the given numbers with the given message.

        ``on_result(number, ok, error)`` is invoked once per recipient so the
        caller can record a per-recipient outcome instead of assuming that a
        batch which raised nothing delivered everything.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the sender backend is available and ready."""
        ...


class PhoneLinkSender(SMSSender):
    def __init__(self, on_log=None):
        from automation.phone_link import PhoneLinkSender as _PhoneLinkAutomation
        self._automation = _PhoneLinkAutomation(on_log=on_log)

    def send(self, numbers: list[str], message: str, on_result=None) -> None:
        self._automation.send_batch(numbers, message, on_result=on_result)

    def is_available(self) -> bool:
        return self._automation.is_available()
