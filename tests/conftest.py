import os
from pathlib import Path
import pytest


@pytest.fixture
def fake_proc(tmp_path):
    def _build(pids, net_files=None):
        root = tmp_path
        # create pid trees
        for p in pids:
            pid_dir = root / str(p["pid"])
            pid_dir.mkdir()
            (pid_dir / "comm").write_text(p.get("comm", ""), encoding="utf8")
            if "exe" in p and p["exe"] is not None:
                try:
                    os.symlink(p["exe"], pid_dir / "exe")
                except FileExistsError:
                    pass
            cmd = p.get("cmdline", "")
            (pid_dir / "cmdline").write_bytes(cmd.replace("\x00", "\x00").encode("utf8"))
            uid = p.get("uid", 0)
            (pid_dir / "status").write_text(f"Name:\t{p.get('comm','')}\nUid:\t{uid}\t0\t0\t0\n", encoding="utf8")
            fd_dir = pid_dir / "fd"
            fd_dir.mkdir()
            for fd in p.get("fds", []):
                target = fd["target"]
                fd_path = fd_dir / str(fd["fd_num"])
                os.symlink(target, fd_path)

        # create net files if provided
        if net_files:
            net_dir = tmp_path / "net"
            net_dir.mkdir()
            for name, content in net_files.items():
                (net_dir / name).write_text(content, encoding="utf8")

        return str(root)

    return _build
