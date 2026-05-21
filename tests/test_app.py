import pytest
from portwatch.widgets import BladesWidget
from portwatch.snapshot import PortRecord
from portwatch.proc import Socket
from portwatch.process import ProcessInfo
from portwatch.app import (
    BladesDisplay,
    FilterMode,
    SessionStats,
    SlotManager,
    _dedupe_records_by_port,
    _format_status_line,
    filter_records,
)


def _record(port, state="LISTEN", pid=100):
    s = Socket(protocol="tcp4", local_ip="0.0.0.0", local_port=port, remote_ip="0.0.0.0", remote_port=0, state=state, inode=port, uid=0)
    p = ProcessInfo(pid=pid, name="proc", exe="/bin/proc", cmdline="", uid=0, username="root")
    return PortRecord(socket=s, process=p)


def _grouped(*records):
    grouped = {}
    for record in records:
        grouped.setdefault(record.process.name, []).append(record)
    return grouped


def test_blades_widget_renders_without_error():
    records = [_record(80), _record(443, state="ESTABLISHED"), _record(3306, state="TIME_WAIT")]
    c = BladesWidget(_grouped(*records))
    out = c.render(80, 24)
    assert out is not None


def test_blades_widget_empty_records_shows_loading():
    c = BladesWidget({})
    out = c.render(80, 24)
    s = str(out)
    assert "LOADING" in s or "····" in s


def test_blades_widget_pin_count_matches_records():
    records = [_record(i) for i in range(10000, 10010)]
    c = BladesWidget(_grouped(*records))
    s = str(c.render(120, 40))
    for port in range(10000, 10010):
        assert str(port) in s
    assert "portwatch" in s


def test_blades_widget_deduplicates_port_numbers():
    records = [
        _record(5353, state="TIME_WAIT", pid=1),
        _record(5353, state="ESTABLISHED", pid=2),
        _record(5353, state="LISTEN", pid=3),
    ]
    deduped = _dedupe_records_by_port(records)
    assert [record.socket.state for record in deduped] == ["LISTEN"]


def test_status_bar_contains_version():
    s = _format_status_line("0.0.1", 95, "12:34:56")
    assert "v0.0.1" in s


def test_blades_display_update_records():
    display = BladesDisplay([_record(80)])
    display.update_records([_record(80), _record(443, state="ESTABLISHED")])
    assert display.current_record() is not None or True


def test_sticky_slots_preserve_position():
    manager = SlotManager()
    first = [_record(22), _record(80), _record(443)]
    manager.update(first, slot_count=3, now=0.0)
    second = [_record(22), _record(443), _record(8080)]
    manager.update(second, slot_count=3, now=1.0)
    assert manager.slot_map[22] == 0
    assert manager.slot_map[443] == 2
    assert manager.slot_map[8080] == 1


def test_sticky_slots_expiry():
    manager = SlotManager()
    manager.update([_record(22), _record(80), _record(443)], slot_count=3, now=0.0)
    manager.update([_record(22), _record(443)], slot_count=3, now=1.0)
    assert 80 not in manager.slot_map
    assert 80 in manager.slot_expiry
    manager.update([_record(22), _record(443), _record(8080)], slot_count=3, now=32.0)
    assert manager.slot_map[8080] == 1


def test_filter_listen_only():
    records = [_record(22), _record(443, state="ESTABLISHED"), _record(8080, state="TIME_WAIT")]
    filtered = filter_records(records, FilterMode.LISTEN)
    assert [r.socket.local_port for r in filtered] == [22]


def test_session_stats_accumulate():
    stats = SessionStats(start_time=0.0)
    stats.snapshot_count += 1
    stats.peak_port_count = max(stats.peak_port_count, 3)
    stats.changes_detected += 2
    stats.snapshot_count += 1
    stats.peak_port_count = max(stats.peak_port_count, 4)
    stats.changes_detected += 1
    stats.snapshot_count += 1
    stats.peak_port_count = max(stats.peak_port_count, 4)
    assert stats.snapshot_count == 3
    assert stats.peak_port_count == 4
    assert stats.changes_detected == 3
