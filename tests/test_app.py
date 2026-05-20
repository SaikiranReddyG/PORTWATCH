import pytest
from portwatch.widgets.chip import ChipWidget
from portwatch.snapshot import PortRecord
from portwatch.proc import Socket
from portwatch.process import ProcessInfo
from portwatch.app import _format_status_line


def _record(port, state="LISTEN", pid=100):
    s = Socket(protocol="tcp4", local_ip="0.0.0.0", local_port=port, remote_ip="0.0.0.0", remote_port=0, state=state, inode=port, uid=0)
    p = ProcessInfo(pid=pid, name="proc", exe="/bin/proc", cmdline="", uid=0, username="root")
    return PortRecord(socket=s, process=p)


def test_chip_widget_renders_without_error():
    records = [_record(80), _record(443, state="ESTABLISHED"), _record(3306, state="TIME_WAIT")]
    c = ChipWidget(records)
    out = c.render(80, 24)
    assert out is not None


def test_chip_widget_empty_records_shows_loading():
    c = ChipWidget([])
    out = c.render(80, 24)
    s = str(out)
    assert "LOADING" in s or "····" in s


def test_chip_widget_pin_count_matches_records():
    records = [_record(i) for i in range(10000, 10010)]
    c = ChipWidget(records)
    s = str(c.render(120, 40))
    for port in range(10000, 10008):
        assert str(port) in s
    assert "+2 more" in s
    assert "10008" not in s
    assert "10009" not in s


def test_status_bar_contains_version():
    s = _format_status_line("0.0.1", 95, "12:34:56")
    assert "v0.0.1" in s
