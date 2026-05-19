from pathlib import Path

import pytest


def test_take_snapshot_joins_socket_and_process(fake_proc):
    # prepare a tcp file with one socket (inode 5555) and a pid that owns it
    tcp = (
        "sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
        "  0: 0100007F:0050 00000000:0000 0A 00000000:00000000 00:00000000 00000000   1000        0 5555 1 0000000000000000 100 0 0 10 0\n"
    )
    p = {"pid": 600, "comm": "svc", "exe": "/usr/sbin/svc", "cmdline": "svc", "uid": 1000, "fds": [{"fd_num": 3, "target": "socket:[5555]"}]}
    root = fake_proc([p], net_files={"tcp": tcp})

    from portwatch.snapshot import take_snapshot

    snap = take_snapshot(proc_root=root)
    assert len(snap) == 1
    rec = snap[0]
    assert rec.socket.inode == 5555
    assert rec.process is not None
    assert rec.process.pid == 600
    assert rec.process_name == "svc"


def test_take_snapshot_unresolved_process_is_none(fake_proc):
    tcp = (
        "sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
        "  0: 0100007F:1F90 00000000:0000 0A 00000000:00000000 00:00000000 00000000   1000        0 7777 1 0000000000000000 100 0 0 10 0\n"
    )
    # no pid owns inode 7777
    root = fake_proc([], net_files={"tcp": tcp})

    from portwatch.snapshot import take_snapshot

    snap = take_snapshot(proc_root=root)
    assert len(snap) == 1
    rec = snap[0]
    assert rec.process is None
    assert rec.process_name == "???"


def test_take_snapshot_multiple_protocols(fake_proc):
    tcp = "sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
    tcp6 = tcp
    udp = tcp
    udp6 = tcp
    root = fake_proc([], net_files={"tcp": tcp, "tcp6": tcp6, "udp": udp, "udp6": udp6})
    from portwatch.snapshot import take_snapshot
    snap = take_snapshot(proc_root=root)
    # header-only files → 0 sockets
    assert len(snap) == 0


def test_take_snapshot_empty_system(fake_proc):
    # empty net files (only header)
    header = "sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
    root = fake_proc([], net_files={"tcp": header, "tcp6": header, "udp": header, "udp6": header})
    from portwatch.snapshot import take_snapshot
    snap = take_snapshot(proc_root=root)
    assert snap == []


def test_take_snapshot_preserves_order(fake_proc):
    # create three lines in order: ports 80, 22, 443
    lines = (
        "sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
        "  0: 0100007F:0050 00000000:0000 0A 00000000:00000000 00:00000000 00000000   1000        0 100 1 0000000000000000 100 0 0 10 0\n"
        "  1: 0100007F:0016 00000000:0000 0A 00000000:00000000 00:00000000 00000000   1000        0 200 1 0000000000000000 100 0 0 10 0\n"
        "  2: 0100007F:01BB 00000000:0000 0A 00000000:00000000 00:00000000 00000000   1000        0 300 1 0000000000000000 100 0 0 10 0\n"
    )
    root = fake_proc([], net_files={"tcp": lines})
    from portwatch.snapshot import take_snapshot
    snap = take_snapshot(proc_root=root)
    ports = [r.local_port for r in snap]
    assert ports == [80, 22, 443]


def test_convenience_properties():
    from portwatch.proc import Socket
    from portwatch.snapshot import PortRecord

    s = Socket(protocol="tcp4", local_ip="1.2.3.4", local_port=80, remote_ip="0.0.0.0", remote_port=0, state="LISTEN", inode=0, uid=0)
    pr = PortRecord(socket=s, process=None)
    assert pr.protocol == "tcp4"
    assert pr.process_name == "???"


def test_read_all_accepts_proc_root(fake_proc):
    # ensure read_all reads net files from custom proc_root
    header = "sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
    root = fake_proc([], net_files={"tcp": header})
    from portwatch.proc import read_all
    socks = read_all(proc_root=root)
    assert isinstance(socks, list)
