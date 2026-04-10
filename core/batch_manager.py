class BatchManager:
    def __init__(self, numbers: list[str], batch_size: int = 20):
        self._numbers = list(numbers)
        self._batch_size = batch_size
        self._batches: list[list[str]] = []
        self._statuses: list[str] = []
        self._errors: list[str | None] = []

        for i in range(0, len(self._numbers), self._batch_size):
            self._batches.append(self._numbers[i : i + self._batch_size])
            self._statuses.append("pending")
            self._errors.append(None)

    @property
    def total_batches(self) -> int:
        return len(self._batches)

    def get_batch(self, index: int) -> list[str]:
        return self._batches[index]

    def get_status(self, index: int) -> str:
        return self._statuses[index]

    def mark_sent(self, index: int) -> None:
        self._statuses[index] = "sent"

    def mark_error(self, index: int, reason: str) -> None:
        self._statuses[index] = "error"
        self._errors[index] = reason

    def next_pending_index(self) -> int | None:
        """Return index of next batch to send (pending or error). None if all sent."""
        for i, status in enumerate(self._statuses):
            if status != "sent":
                return i
        return None

    def summary(self) -> dict:
        return {
            "total": self.total_batches,
            "sent": self._statuses.count("sent"),
            "error": self._statuses.count("error"),
            "pending": self._statuses.count("pending"),
        }
