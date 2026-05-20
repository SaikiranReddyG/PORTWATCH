import time
from portwatch.loop import SessionStats, _format_change, _format_summary, _format_baseline
from portwatch.snapshot import PortRecord
from portwatch.proc import Socket
from portwatch.process import ProcessInfo


def _make_record(**kwargs) -> PortRecord:
    s = Socket(
        protocol=kwargs.get("protocol", "tcp4"),
        local_ip=kwargs.get("local_ip", "0.0.0.0"),
        local_port=kwargs.get("local_port", 80),
        remote_ip=kwargs.get("remote_ip", "0.0.0.0"),
        remote_port=kwargs.get("remote_port", 0),
        state=kwargs.get("state", "LISTEN"),
        inode=kwargs.get("inode", 1000),
        uid=kwargs.get("uid", 0),
    )
    p = None
    if not kwargs.get("process_none", False):
        p = ProcessInfo(pid=kwargs.get("pid", 100), name=kwargs.get("process_name", "nginx"), exe=kwargs.get("exe", "/usr/sbin/nginx"), cmdline="", uid=kwargs.get("uid", 0), username="root")
    return PortRecord(socket=s, process=p)


def test_session_stats_defaults():
    s = SessionStats(start_time=time.time())
    assert s.snapshot_count == 0
    assert s.peak_port_count == 0
    assert s.suspicious_count == 0
    assert s.parse_error_count == 0
    assert s.changes_detected == 0


def test_format_added_line():
    r = _make_record(local_port=9999)
    line = _format_change("+", r, None, timestr="00:00:00")
    assert "+" in line and "tcp4" in line and ":9999" in line and "nginx" in line


def test_format_removed_line():
    r = _make_record(local_port=8888)
    line = _format_change("-", r, None, timestr="00:00:01")
    assert line.startswith("[00:00:01] -") and ":8888" in line


def test_format_changed_line():
    prev = _make_record(local_port=80, state="LISTEN", pid=100, process_name="nginx")
    curr = _make_record(local_port=80, state="ESTABLISHED", pid=200, process_name="apache")
    line = _format_change("~", curr, prev, timestr="00:00:02")
    assert "LISTEN→ESTABLISHED" in line and "nginx→apache" in line


def test_format_unresolved_process():
    r = _make_record(process_none=True)
    line = _format_change("+", r, None, timestr="00:00:03")
    assert "???" in line


def test_exit_summary_format():
    s = SessionStats(start_time=time.time() - 227)
    s.snapshot_count = 5
    s.peak_port_count = 10
    s.changes_detected = 3
    s.suspicious_count = 0
    s.parse_error_count = 0
    txt = _format_summary(s, runtime_seconds=227)
    assert "3m 47s" in txt


def test_exit_summary_short_runtime():
    s = SessionStats(start_time=time.time() - 5)
    txt = _format_summary(s, runtime_seconds=5)
    assert "5s" in txt


def test_exit_summary_long_runtime():
    s = SessionStats(start_time=time.time() - 3661)
    txt = _format_summary(s, runtime_seconds=3661)
    assert "1h 1m 1s" in txt


def test_baseline_summary_counts():
    snap = [
        _make_record(local_port=1, state="LISTEN"),
        _make_record(local_port=2, state="LISTEN"),
        _make_record(local_port=3, state="LISTEN"),
        _make_record(local_port=4, state="LISTEN"),
        _make_record(local_port=5, state="LISTEN"),
        _make_record(local_port=6, state="ESTABLISHED"),
        _make_record(local_port=7, state="ESTABLISHED"),
        _make_record(local_port=8, state="ESTABLISHED"),
        _make_record(local_port=9, state="TIME_WAIT"),
        _make_record(local_port=10, state="CLOSE"),
    ]
    line = _format_baseline(snap, timestr="00:00:04")
    assert "10 sockets (5 LISTEN, 3 ESTABLISHED, 2 other)" in line
