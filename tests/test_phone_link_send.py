"""Regression tests for the Phone Link single-SMS send flow.

Background — the bug these tests pin down:

On the first send of a run, the New Message pane opens but the recipient and
message body are never typed, and the SMS is silently NOT sent. The batch is
still reported as "sent", so the recipient is skipped on the next run.

Two defects made that possible:

1. ``_reacquire_window`` claimed to wait for the compose pane, but it only
   resolved the *main* Phone Link window — which always exists — so it returned
   instantly. The flow then raced a cold, still-initialising compose pane.
2. Nothing in the flow verified that the recipient or the body actually landed
   in the UI before pressing ENTER, so a lost keystroke looked like success.

The fake Phone Link below models a compose pane that needs a few UIA polls to
appear and that drops the keystrokes of the very first compose — exactly the
cold-start behaviour reported from the live app.
"""
from types import SimpleNamespace

import pytest

pytest.importorskip("win32clipboard")  # automation.phone_link imports it

import automation.phone_link as pl
from automation.phone_link import PhoneLinkAutomationError, PhoneLinkSender


class FakeElement:
    def __init__(self, app, name, kind):
        self._app = app
        self._kind = kind
        self.element_info = SimpleNamespace(name=name)

    def is_enabled(self):
        return True

    def is_visible(self):
        return True

    def wait(self, state, timeout=None):
        return self

    def click_input(self):
        self._app.click(self._kind)

    def type_keys(self, keys, **kwargs):
        self._app.send_keys(keys, target=self._kind)

    def get_value(self):
        return self._app.values[self._kind]


class FakeWindow:
    """Stands in for both the WindowSpecification and its wrapper object."""

    def __init__(self, app):
        self._app = app

    def wait(self, state, timeout=None):
        return self

    def set_focus(self):
        return self

    def wrapper_object(self):
        return self

    def type_keys(self, keys, **kwargs):
        self._app.send_keys(keys)

    def child_window(self, title_re=None, title=None, control_type=None, **kwargs):
        return FakeElement(self._app, title or "Messages", "tab")

    def descendants(self, control_type=None):
        if control_type != "Edit":
            return []
        return self._app.edit_fields()


class FakeApp:
    """A Phone Link stand-in with a compose pane that is slow and cold-starts badly.

    ``open_polls`` — how many UIA descendant scans pass before the compose pane
    shows up in the tree (a cold pane needs several).
    ``deaf_composes`` — how many freshly opened compose panes ignore keystrokes
    entirely, reproducing the lost first recipient.
    """

    def __init__(self, open_polls=3, deaf_composes=1, tab_navigates=True):
        self._open_polls = open_polls
        self._deaf_composes = deaf_composes
        self._tab_navigates = tab_navigates
        self._polls_left = 0
        self.compose_open = False
        self.compose_deaf = False
        self.composes_opened = 0
        self.focus = None
        self.values = {"to": "", "msg": ""}
        self.recipient_committed = False
        self.sent = []
        self.clipboard = ""

    # -- UIA surface -----------------------------------------------------
    def edit_fields(self):
        if not self.compose_open:
            return []
        if self._polls_left > 0:
            self._polls_left -= 1
            return []
        return [
            FakeElement(self, "To", "to"),
            FakeElement(self, "Send a message", "msg"),
        ]

    def click(self, kind):
        if self.compose_deaf:
            self.focus = None
            return
        self.focus = kind

    # -- keyboard --------------------------------------------------------
    def send_keys(self, keys, target=None):
        if target is not None:
            self.click(target)

        if keys == "^n":
            self._open_compose()
            return
        if self.compose_deaf:
            return
        if keys == "{ESC}":
            self._close_compose()
            return
        if keys == "{TAB}":
            if self._tab_navigates:
                self.focus = "msg" if self.focus in ("to", None) else self.focus
            return
        if keys == "{ENTER}":
            self._enter()
            return
        if keys == "^v":
            if self.focus:
                self.values[self.focus] += self.clipboard
            return
        if self.focus:
            self.values[self.focus] += keys.replace("{+}", "+")

    def _open_compose(self):
        self.composes_opened += 1
        self.compose_open = True
        self.compose_deaf = self.composes_opened <= self._deaf_composes
        self._polls_left = self._open_polls
        self.focus = None
        self.values = {"to": "", "msg": ""}
        self.recipient_committed = False

    def _close_compose(self):
        self.compose_open = False
        self.compose_deaf = False
        self.focus = None

    def _enter(self):
        if self.focus == "to" and self.values["to"]:
            self.recipient_committed = True
        elif self.focus == "msg" and self.recipient_committed and self.values["msg"]:
            self.sent.append((self.values["to"], self.values["msg"]))
            self._close_compose()


@pytest.fixture
def fake_app(monkeypatch):
    app = FakeApp()
    monkeypatch.setattr(pl, "Desktop", lambda backend=None: SimpleNamespace(
        window=lambda **kwargs: FakeWindow(app)
    ))
    monkeypatch.setattr(pl, "_set_clipboard", lambda text: setattr(app, "clipboard", text))
    monkeypatch.setattr(pl, "_save_clipboard", lambda: None)
    monkeypatch.setattr(pl, "_restore_clipboard", lambda text: None)
    monkeypatch.setattr(pl.time, "sleep", lambda seconds: None)
    return app


class TestColdStartFirstRecipient:
    def test_first_recipient_is_actually_sent(self, fake_app):
        """The reported bug: first compose swallows input, SMS never goes out."""
        PhoneLinkSender()._send_single("+48512345678", "Dzien dobry")

        assert fake_app.sent == [("+48512345678", "Dzien dobry")]

    def test_batch_does_not_lose_its_first_number(self, fake_app):
        numbers = ["+48111111111", "+48222222222", "+48333333333"]
        PhoneLinkSender().send_batch(numbers, "Tresc")

        assert [number for number, _ in fake_app.sent] == numbers


class TestMessageFieldIsClickedNotTabbedTo:
    """Live logs showed the recipient landing fine and the body not.

    Two blind TABs were used to reach the message field; on a cold compose pane
    they do not land there, so Ctrl+V went nowhere. The "To" field was always
    clicked directly and never had this problem — the body field now is too.
    """

    def test_sends_even_when_tab_navigation_does_not_work(self, fake_app):
        fake_app._tab_navigates = False

        PhoneLinkSender()._send_single("+48512345678", "Tresc SMS-a")

        assert fake_app.sent == [("+48512345678", "Tresc SMS-a")]

    def test_body_lands_on_the_first_attempt(self, fake_app):
        """No retries needed for the body once the field is clicked."""
        fake_app._tab_navigates = False
        fake_app._deaf_composes = 0  # a warm pane: nothing should fail at all

        PhoneLinkSender()._send_single("+48512345678", "Tresc SMS-a")

        assert fake_app.composes_opened == 1


class TestFailuresAreNeverSilent:
    def test_raises_when_recipient_never_lands(self, fake_app):
        fake_app._deaf_composes = 99  # compose never accepts input

        with pytest.raises(PhoneLinkAutomationError):
            PhoneLinkSender()._send_single("+48512345678", "Tresc")

        assert fake_app.sent == []

    def test_batch_reports_each_recipient(self, fake_app):
        results = []
        PhoneLinkSender().send_batch(
            ["+48111111111", "+48222222222"],
            "Tresc",
            on_result=lambda number, ok, error: results.append((number, ok)),
        )

        assert results == [("+48111111111", True), ("+48222222222", True)]

    def test_batch_reports_failure_and_continues(self, fake_app):
        results = []
        original = PhoneLinkSender._send_single

        def flaky(self, number, message):
            if number == "+48111111111":
                raise PhoneLinkAutomationError("pole 'Do' puste")
            return original(self, number, message)

        PhoneLinkSender._send_single = flaky
        try:
            PhoneLinkSender().send_batch(
                ["+48111111111", "+48222222222"],
                "Tresc",
                on_result=lambda number, ok, error: results.append((number, ok)),
            )
        finally:
            PhoneLinkSender._send_single = original

        assert results == [("+48111111111", False), ("+48222222222", True)]
        assert [number for number, _ in fake_app.sent] == ["+48222222222"]

    def test_batch_raises_when_no_callback_watches_results(self, fake_app):
        fake_app._deaf_composes = 99

        with pytest.raises(PhoneLinkAutomationError):
            PhoneLinkSender().send_batch(["+48512345678"], "Tresc")


class TestComposeWait:
    def test_does_not_return_before_the_to_field_exists(self, fake_app):
        fake_app._open_compose()
        fake_app.compose_deaf = False
        polls = fake_app._polls_left
        assert polls > 0

        win, to_field = PhoneLinkSender()._wait_for_compose()

        assert to_field.element_info.name == "To"
        assert fake_app._polls_left == 0  # it really waited out the cold scans

    def test_raises_when_compose_never_opens(self, fake_app, monkeypatch):
        monkeypatch.setattr(pl, "_wait_until", lambda predicate, timeout, **kwargs: None)

        with pytest.raises(PhoneLinkAutomationError):
            PhoneLinkSender()._wait_for_compose()
