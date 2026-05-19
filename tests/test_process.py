import os
import stat
import pwd
import shutil
import logging
from pathlib import Path

import pytest


def _build_fake_proc(tmp_path: Path, pids: list[dict]) -> str:
    root = tmp_path
    for p in pids:
        pid_dir = root / str(p["pid"])
        pid_dir.mkdir()
        # comm
        (pid_dir / "comm").write_text(p.get("comm", ""), encoding="utf8")
        # exe (symlink) if provided
        if "exe" in p and p["exe"] is not None:
            try:
                os.symlink(p["exe"], pid_dir / "exe")
            except FileExistsError:
                pass
        # cmdline: write null-separated
        cmd = p.get("cmdline", "")
        (pid_dir / "cmdline").write_bytes(cmd.replace("\x00", "\x00").encode("utf8"))
        # status with Uid:
        uid = p.get("uid", 0)
        (pid_dir / "status").write_text(f"Name:\t{p.get('comm','')}\nUid:\t{uid}\t0\t0\t0\n", encoding="utf8")
        # fd dir
        fd_dir = pid_dir / "fd"
        fd_dir.mkdir()
        for fd in p.get("fds", []):
            target = fd["target"]
            fd_path = fd_dir / str(fd["fd_num"])
            os.symlink(target, fd_path)
    return str(root)


def test_build_inode_map_finds_socket_inodes(tmp_path):
    from portwatch.process import _build_inode_map

    pids = [
        {
            "pid": 100,
            "comm": "proc100",
            "exe": "/bin/proc100",
            "cmdline": "proc100",
            "uid": 1000,
            "fds": [{"fd_num": 3, "target": "socket:[111]"}, {"fd_num": 4, "target": "pipe:[222]"}],
        },
        {
            "pid": 200,
            "comm": "proc200",
            "exe": "/bin/proc200",
            "cmdline": "proc200",
            "uid": 1000,
            "fds": [{"fd_num": 3, "target": "socket:[333]"}, {"fd_num": 4, "target": "anon_inode:[eventfd]"}],
        },
    ]
    root = _build_fake_proc(tmp_path, pids)
    m = _build_inode_map(root)
    assert m[111] == 100
    assert m[333] == 200
    assert 222 not in m


def test_build_inode_map_skips_permission_error(tmp_path):
    from portwatch.process import _build_inode_map

    pids = [
        {
            "pid": 101,
            "comm": "proc101",
            "exe": "/bin/proc101",
            "cmdline": "proc101",
            "uid": 1000,
            "fds": [{"fd_num": 3, "target": "socket:[444]"}],
        },
        {
            "pid": 102,
            "comm": "proc102",
            "exe": "/bin/proc102",
            "cmdline": "proc102",
            "uid": 1000,
            "fds": [{"fd_num": 3, "target": "socket:[555]"}],
        },
    ]
    root = Path(_build_fake_proc(tmp_path, pids))
    # make pid 102 fd dir unreadable
    fd_dir = root / "102" / "fd"
    fd_dir.chmod(0)
    try:
        m = _build_inode_map(str(root))
    finally:
        fd_dir.chmod(0o755)
    assert 444 in m
    # 555 may be missing due to permission; ensure no exception and other entries present


def test_resolve_pid_full_info(tmp_path):
    from portwatch.process import _resolve_pid

    p = {
        "pid": 201,
        "comm": "myp",
        "exe": "/usr/bin/myp",
        "cmdline": "myp --serve",
        "uid": 1000,
        "fds": [],
    }
    root = _build_fake_proc(tmp_path, [p])
    pi = _resolve_pid(201, root)
    assert pi.pid == 201
    assert pi.name == "myp"
    assert pi.exe.endswith("/usr/bin/myp")
    assert "myp --serve" in pi.cmdline
    assert pi.uid == 1000


def test_resolve_pid_missing_exe(tmp_path):
    from portwatch.process import _resolve_pid

    p = {
        "pid": 202,
        "comm": "noexe",
        # no exe
        "cmdline": "noexe",
        "uid": 1000,
        "fds": [],
    }
    root = _build_fake_proc(tmp_path, [p])
    # remove exe if present
    exe_path = Path(root) / "202" / "exe"
    if exe_path.exists():
        exe_path.unlink()
    pi = _resolve_pid(202, root)
    assert pi.exe == "???"
    assert pi.name == "noexe"


def test_resolve_pid_username_fallback(tmp_path, monkeypatch):
    from portwatch.process import _resolve_pid

    p = {"pid": 203, "comm": "u", "exe": "/bin/u", "cmdline": "u", "uid": 99999, "fds": []}
    root = _build_fake_proc(tmp_path, [p])
    # ensure getpwuid will fail
    import pwd as _pwd

    monkeypatch.setattr(_pwd, "getpwuid", lambda uid: (_ for _ in ()).throw(KeyError()))
    pi = _resolve_pid(203, root)
    assert pi.username == "uid:99999"


def test_resolve_inode_found(tmp_path):
    from portwatch.process import resolve_inode

    p = {"pid": 301, "comm": "s", "exe": "/bin/s", "cmdline": "s", "uid": 1000, "fds": [{"fd_num": 3, "target": "socket:[777]"}]}
    root = _build_fake_proc(tmp_path, [p])
    pi = resolve_inode(777, root)
    assert pi is not None
    assert pi.pid == 301


def test_resolve_inode_not_found(tmp_path):
    from portwatch.process import resolve_inode

    p = {"pid": 302, "comm": "s2", "exe": "/bin/s2", "cmdline": "s2", "uid": 1000, "fds": []}
    root = _build_fake_proc(tmp_path, [p])
    pi = resolve_inode(8888, root)
    assert pi is None


def test_resolve_inodes_batch(tmp_path):
    from portwatch.process import resolve_inodes

    p1 = {"pid": 401, "comm": "a", "exe": "/bin/a", "cmdline": "a", "uid": 1000, "fds": [{"fd_num": 3, "target": "socket:[1001]"}]}
    p2 = {"pid": 402, "comm": "b", "exe": "/bin/b", "cmdline": "b", "uid": 1000, "fds": [{"fd_num": 3, "target": "socket:[1002]"}, {"fd_num": 4, "target": "socket:[1003]"}]}
    root = _build_fake_proc(tmp_path, [p1, p2])
    res = resolve_inodes({1001, 1002, 1003, 9999}, root)
    assert set(res.keys()) == {1001, 1002, 1003}


def test_cmdline_null_bytes_replaced(tmp_path):
    from portwatch.process import _resolve_pid

    p = {"pid": 501, "comm": "py", "exe": "/usr/bin/py", "cmdline": "python3\x00-m\x00http.server", "uid": 1000, "fds": []}
    root = _build_fake_proc(tmp_path, [p])
    pi = _resolve_pid(501, root)
    assert pi.cmdline == "python3 -m http.server"
