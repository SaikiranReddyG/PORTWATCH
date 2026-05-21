import pytest

from portwatch.diff import diff_snapshots, SnapshotDiff
from portwatch.snapshot import PortRecord
from portwatch.proc import Socket
from portwatch.process import ProcessInfo


def _make_record(
    protocol: str = "tcp4",
    local_ip: str = "0.0.0.0",
    local_port: int = 80,
    remote_ip: str = "0.0.0.0",
    remote_port: int = 0,
    state: str = "LISTEN",
    inode: int = 1000,
    uid: int = 0,
    pid: int = 100,
    process_name: str = "nginx",
    exe: str = "/usr/sbin/nginx",
) -> PortRecord:
    s = Socket(
        protocol=protocol,
        local_ip=local_ip,
        local_port=local_port,
        remote_ip=remote_ip,
        remote_port=remote_port,
        state=state,
        inode=inode,
        uid=uid,
    )
    p = ProcessInfo(pid=pid, name=process_name, exe=exe, cmdline=exe, uid=uid, username=f"uid:{uid}")
    return PortRecord(socket=s, process=p)


def test_identical_snapshots_diff_is_empty():
    a = [_make_record(local_port=80), _make_record(local_port=443, inode=1001)]
    d = diff_snapshots(a, list(a))
    assert isinstance(d, SnapshotDiff)
    assert d.is_empty


def test_new_port_detected_as_added():
    prev = [_make_record(local_port=80)]
    curr = [_make_record(local_port=80), _make_record(local_port=443, inode=1001)]
    d = diff_snapshots(prev, curr)
    assert len(d.added) == 1
    assert d.added[0].local_port == 443


def test_closed_port_detected_as_removed():
    prev = [_make_record(local_port=80), _make_record(local_port=443, inode=1001)]
    curr = [_make_record(local_port=80)]
    d = diff_snapshots(prev, curr)
    assert len(d.removed) == 1
    assert d.removed[0].local_port == 443


def test_state_change_detected():
    prev = [_make_record(local_port=80, state="LISTEN")]
    curr = [_make_record(local_port=80, state="ESTABLISHED")]
    d = diff_snapshots(prev, curr)
    assert len(d.changed) == 1
    assert d.changed[0][0].state == "LISTEN"
    assert d.changed[0][1].state == "ESTABLISHED"


def test_process_change_detected():
    prev = [_make_record(local_port=80, pid=100, process_name="nginx")]
    curr = [_make_record(local_port=80, pid=200, process_name="apache")]
    d = diff_snapshots(prev, curr)
    assert len(d.changed) == 1
    assert d.changed[0][0].process_name == "nginx"
    assert d.changed[0][1].process_name == "apache"


def test_pid_change_same_process_name_detected():
    prev = [_make_record(local_port=80, pid=100, process_name="nginx")]
    curr = [_make_record(local_port=80, pid=200, process_name="nginx")]
    d = diff_snapshots(prev, curr)
    assert len(d.changed) == 1


def test_remote_endpoint_change_detected():
    prev = [_make_record(local_port=80, remote_ip="1.2.3.4", remote_port=5000)]
    curr = [_make_record(local_port=80, remote_ip="5.6.7.8", remote_port=6000)]
    d = diff_snapshots(prev, curr)
    assert len(d.changed) == 1


def test_uid_change_alone_not_detected():
    prev = [_make_record(local_port=80, uid=0)]
    curr = [_make_record(local_port=80, uid=33)]
    d = diff_snapshots(prev, curr)
    assert d.is_empty


def test_multiple_changes_at_once():
    a = _make_record(local_port=80)
    b = _make_record(local_port=81)
    c_prev = _make_record(local_port=82, state="LISTEN")
    c_curr = _make_record(local_port=82, state="ESTABLISHED")
    prev = [a, b, c_prev]
    curr = [a, c_curr, _make_record(local_port=443, inode=9999)]
    d = diff_snapshots(prev, curr)
    assert len(d.added) == 1
    assert len(d.removed) == 1
    assert len(d.changed) == 1


def test_empty_previous_all_added():
    prev = []
    curr = [_make_record(local_port=10), _make_record(local_port=11), _make_record(local_port=12)]
    d = diff_snapshots(prev, curr)
    assert len(d.added) == 3


def test_empty_current_all_removed():
    prev = [_make_record(local_port=10), _make_record(local_port=11), _make_record(local_port=12)]
    curr = []
    d = diff_snapshots(prev, curr)
    assert len(d.removed) == 3


def test_both_empty_is_empty():
    d = diff_snapshots([], [])
    assert d.is_empty
