import pytest

from core.sender import SMSSender


class FakeSender(SMSSender):
    def __init__(self):
        self.sent = []

    def send(self, numbers: list[str], message: str) -> None:
        self.sent.append({"numbers": numbers, "message": message})

    def is_available(self) -> bool:
        return True


class TestSMSSenderInterface:
    def test_fake_sender_implements_interface(self):
        sender = FakeSender()
        sender.send(["+48512345678"], "Test")
        assert len(sender.sent) == 1
        assert sender.sent[0]["numbers"] == ["+48512345678"]
        assert sender.sent[0]["message"] == "Test"

    def test_is_available(self):
        sender = FakeSender()
        assert sender.is_available() is True

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            SMSSender()
