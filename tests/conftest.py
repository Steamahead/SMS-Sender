import tempfile

import pytest


@pytest.fixture(autouse=True)
def _isolate_tempdir(tmp_path, monkeypatch):
    """Redirect tempfile.mkdtemp()/mkstemp() into pytest's per-test tmp_path.

    The tests create scratch files via ``tempfile.mkdtemp()`` without a
    ``dir=`` argument. Depending on the environment that can resolve to the
    project root and, because mkdtemp never cleans up after itself, leaves
    hundreds of stray ``tmpXXXXXXXX`` directories behind. Pointing
    ``tempfile.tempdir`` at pytest's ``tmp_path`` keeps every scratch dir
    inside a location pytest removes automatically after the test run.
    """
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    yield
