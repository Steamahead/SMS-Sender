"""Dragging a text box's corner grip grows it inside its layout."""
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QDialog, QSplitter, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtCore import Qt


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _splitter(app, sizes):
    sp = QSplitter(Qt.Orientation.Vertical)
    boxes = []
    for _ in sizes:
        box = QTextEdit()
        box.setMinimumHeight(40)
        sp.addWidget(box)
        boxes.append(box)
    sp.resize(300, sum(sizes) + sp.handleWidth() * (len(sizes) - 1))
    sp.show()
    sp.setSizes(sizes)
    app.processEvents()
    return sp, boxes


def test_middle_pane_grows_at_the_expense_of_the_one_below(app):
    from gui.widgets.resize_grip import grow
    sp, boxes = _splitter(app, [100, 100, 100])
    grow(boxes[1], 0, 30)
    assert sp.sizes() == [100, 130, 70]


def test_last_pane_borrows_from_above(app):
    from gui.widgets.resize_grip import grow
    sp, boxes = _splitter(app, [100, 100, 100])
    grow(boxes[2], 0, 30)
    assert sp.sizes() == [100, 70, 130]


def test_shrinking_gives_room_to_the_next_pane(app):
    from gui.widgets.resize_grip import grow
    sp, boxes = _splitter(app, [100, 100, 100])
    grow(boxes[0], 0, -30)
    assert sp.sizes() == [70, 130, 100]


def test_a_pane_never_shrinks_below_its_minimum(app):
    from gui.widgets.resize_grip import grow
    sp, boxes = _splitter(app, [100, 100, 100])
    grow(boxes[0], 0, -500)
    assert sp.sizes()[0] >= 40


def test_box_in_a_dialog_resizes_the_dialog(app):
    from gui.widgets.resize_grip import grow
    dlg = QDialog()
    box = QTextEdit()
    QVBoxLayout(dlg).addWidget(box)
    dlg.resize(400, 300)
    dlg.show()
    app.processEvents()
    grow(box, 50, 40)
    assert (dlg.width(), dlg.height()) == (450, 340)
