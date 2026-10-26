from PySide6.QtWidgets import QWidget, QSplitter, QDialog
from PySide6.QtCore import Qt, QEvent, QPoint, QTimer
from PySide6.QtGui import QPainter, QPen, QColor

from gui.styles import COLORS


class TextResizeGrip(QWidget):
    """A drag handle in the bottom-right corner of a text box.

    Dragging it grows the box the way the user expects from the surrounding
    layout: inside a splitter the box's pane grows and its neighbours give up
    space (the window grows once they are at their minimum); inside a dialog
    the dialog itself is resized, in both directions.
    """

    SIZE = 14

    def __init__(self, text_box: QWidget):
        super().__init__(text_box)
        self._box = text_box
        self._last = None
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setToolTip("Przeciągnij, aby zmienić rozmiar")
        # Keeps the vertical scrollbar clear of the grip (see styles.py).
        text_box.setProperty("resizeGrip", True)
        text_box.installEventFilter(self)
        self._place()
        self.raise_()

    def eventFilter(self, obj, event):
        if obj is self._box and event.type() == QEvent.Type.Resize:
            self._place()
        return False

    def _place(self):
        self.move(self._box.width() - self.SIZE - 2, self._box.height() - self.SIZE - 2)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(COLORS["text_dim"]), 1.4))
        s = self.SIZE
        for offset in (4, 8, 12):
            p.drawLine(QPoint(s - 2, s - offset), QPoint(s - offset, s - 2))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._last is None:
            return
        pos = event.globalPosition().toPoint()
        delta = pos - self._last
        self._last = pos
        grow(self._box, delta.x(), delta.y())

    def mouseReleaseEvent(self, event):
        self._last = None


def add_resize_grip(text_box: QWidget) -> TextResizeGrip:
    return TextResizeGrip(text_box)


def grow(widget: QWidget, dx: int, dy: int) -> None:
    """Make ``widget`` dx wider and dy taller, as far as its layout allows."""
    child = widget
    while not child.isWindow():
        parent = child.parentWidget()
        if isinstance(parent, QSplitter):
            vertical = parent.orientation() == Qt.Orientation.Vertical
            delta = dy if vertical else dx
            if delta:
                leftover, wanted = _shift_splitter(parent, parent.indexOf(child), delta, vertical)
                if leftover and _grow_window(widget.window(), 0 if vertical else leftover,
                                             leftover if vertical else 0):
                    # The splitter would spread the new room over every pane;
                    # once the layout has settled, hand it all to this one.
                    QTimer.singleShot(0, lambda: parent.setSizes(wanted))
            # The other direction is the window's to give, in a dialog.
            window = widget.window()
            if isinstance(window, QDialog):
                _grow_window(window, 0 if not vertical else dx, dy if not vertical else 0)
            return
        child = parent

    window = widget.window()
    if isinstance(window, QDialog):
        _grow_window(window, dx, dy)


def _grow_window(window: QWidget, dx: int, dy: int) -> bool:
    if window.isMaximized() or window.isFullScreen():
        return False
    width, height = window.width() + dx, window.height() + dy

    # Never past the screen edge — the bottom of the window would be lost.
    screen = window.screen()
    if screen is not None:
        avail = screen.availableGeometry()
        frame = window.frameGeometry()
        extra_w = frame.width() - window.width()
        extra_h = frame.height() - window.height()
        width = min(width, max(window.width(), avail.right() + 1 - frame.left() - extra_w))
        height = min(height, max(window.height(), avail.bottom() + 1 - frame.top() - extra_h))

    if (width, height) == (window.width(), window.height()):
        return False
    window.resize(width, height)
    return True


def _min_extent(widget: QWidget, vertical: bool) -> int:
    hint = widget.minimumSizeHint()
    if vertical:
        return max(widget.minimumHeight(), hint.height())
    return max(widget.minimumWidth(), hint.width())


def _shift_splitter(splitter: QSplitter, idx: int, delta: int,
                    vertical: bool) -> tuple[int, list[int]]:
    """Grow pane ``idx`` by ``delta`` (negative shrinks) at its neighbours' expense.

    Returns (leftover, wanted_sizes): leftover is the growth the neighbours
    could not give up, for the caller to take from the window instead;
    wanted_sizes are the pane sizes once that has happened.
    """
    sizes = splitter.sizes()
    n = len(sizes)
    mins = [_min_extent(splitter.widget(i), vertical) for i in range(n)]

    if delta > 0:
        # Panes below give space first; the last pane borrows from above.
        donors = list(range(idx + 1, n)) or list(range(idx - 1, -1, -1))
        need = delta
        for j in donors:
            take = min(max(sizes[j] - mins[j], 0), need)
            sizes[j] -= take
            need -= take
            if not need:
                break
        sizes[idx] += delta - need
        splitter.setSizes(sizes)
        wanted = list(sizes)
        wanted[idx] += need
        return need, wanted

    shrink = min(-delta, max(sizes[idx] - mins[idx], 0))
    receiver = idx + 1 if idx + 1 < n else idx - 1
    sizes[idx] -= shrink
    if receiver >= 0:
        sizes[receiver] += shrink
    splitter.setSizes(sizes)
    return 0, sizes
