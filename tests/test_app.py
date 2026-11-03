import sys
from types import SimpleNamespace

import pytest

from cv_sorter import app


class FakeSerial:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeCapture:
    def __init__(self, opened):
        self.opened = opened
        self.released = False

    def isOpened(self):
        return self.opened

    def release(self):
        self.released = True


def install_fake_runtime(monkeypatch, capture):
    serial_handle = FakeSerial()
    fake_cv2 = SimpleNamespace(
        VideoCapture=lambda _camera: capture,
        destroyAllWindows=lambda: None,
    )
    fake_serial = SimpleNamespace(
        Serial=lambda *_args, **_kwargs: serial_handle,
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    monkeypatch.setitem(sys.modules, "serial", fake_serial)
    monkeypatch.setattr(sys, "argv", ["cv-object-sorter", "--port", "/dev/fake"])
    return serial_handle


def test_serial_port_closes_when_camera_cannot_open(monkeypatch):
    capture = FakeCapture(opened=False)
    serial_handle = install_fake_runtime(monkeypatch, capture)

    with pytest.raises(SystemExit, match="Could not open camera 0"):
        app.run()

    assert capture.released
    assert serial_handle.closed


def test_serial_port_closes_when_color_config_loading_fails(monkeypatch):
    serial_handle = install_fake_runtime(monkeypatch, FakeCapture(opened=True))

    def fail_loading(_path):
        raise ValueError("invalid color config")

    monkeypatch.setattr(app, "load_color_ranges", fail_loading)

    with pytest.raises(ValueError, match="invalid color config"):
        app.run()

    assert serial_handle.closed
