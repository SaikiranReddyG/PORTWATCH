from dataclasses import dataclass
import logging
import os
from typing import Dict, Optional, Set
import pwd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    name: str
    exe: str
    cmdline: str
    uid: int
    username: str


def _build_inode_map(proc_root: str = "/proc") -> Dict[int, int]:
    """Scan proc tree and return a mapping {inode: pid} for socket fds.

    This is intentionally naive and scans every PID; a future optimization
    will build this once and reuse it for many lookups.
    """
    mapping: Dict[int, int] = {}
    try:
        entries = os.listdir(proc_root)
    except Exception:
        logger.debug("failed to list proc root %s", proc_root)
        return mapping

    for name in entries:
        if not name.isdigit():
            continue
        pid = int(name)
        fd_dir = os.path.join(proc_root, name, "fd")
        try:
            fds = os.listdir(fd_dir)
        except (PermissionError, FileNotFoundError, ProcessLookupError) as e:
            logger.debug("skipping pid %s fd dir: %s", name, e)
            continue
        for fd in fds:
            fd_path = os.path.join(fd_dir, fd)
            try:
                target = os.readlink(fd_path)
            except (PermissionError, FileNotFoundError, ProcessLookupError) as e:
                logger.debug("skipping fd %s for pid %s: %s", fd_path, name, e)
                continue
            # target format: socket:[12345]
            if target.startswith("socket:[") and target.endswith("]"):
                try:
                    inode = int(target[len("socket:["):-1])
                except ValueError:
                    continue
                mapping[inode] = pid
    return mapping


def _resolve_pid(pid: int, proc_root: str = "/proc") -> ProcessInfo:
    base = os.path.join(proc_root, str(pid))
    # name
    name = "???"
    try:
        with open(os.path.join(base, "comm"), "r", encoding="utf8") as fh:
            name = fh.read().strip()
    except Exception:
        logger.debug("failed to read comm for pid %s", pid)

    # exe (symlink)
    exe = "???"
    try:
        exe = os.readlink(os.path.join(base, "exe"))
    except Exception:
        logger.debug("failed to read exe for pid %s", pid)

    # cmdline (null-separated)
    cmdline = "???"
    try:
        with open(os.path.join(base, "cmdline"), "rb") as fh:
            raw = fh.read()
            if raw:
                # split on nulls and join with spaces
                parts = raw.split(b"\x00")
                parts = [p.decode("utf8", errors="replace") for p in parts if p]
                cmdline = " ".join(parts)
            else:
                cmdline = ""
    except Exception:
        logger.debug("failed to read cmdline for pid %s", pid)

    # uid from status
    uid = -1
    try:
        with open(os.path.join(base, "status"), "r", encoding="utf8") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            uid = int(parts[1])
                        except Exception:
                            uid = -1
                    break
    except Exception:
        logger.debug("failed to read status for pid %s", pid)

    # username resolution
    username = f"uid:{uid}" if uid >= 0 else "uid:-1"
    try:
        pw = pwd.getpwuid(uid)
        username = pw.pw_name
    except Exception:
        logger.debug("failed to resolve username for uid %s", uid)

    return ProcessInfo(pid=pid, name=name, exe=exe, cmdline=cmdline, uid=uid, username=username)


def resolve_inode(inode: int, proc_root: str = "/proc"):
    mapping = _build_inode_map(proc_root)
    pid = mapping.get(inode)
    if pid is None:
        return None
    return _resolve_pid(pid, proc_root)


def resolve_inodes(inodes: Set[int], proc_root: str = "/proc"):
    """Resolve a batch of inodes by scanning proc once and resolving PIDs.

    Returns a dict {inode: ProcessInfo} for found inodes.
    """
    res = {}
    mapping = _build_inode_map(proc_root)
    for inode in inodes:
        pid = mapping.get(inode)
        if pid is None:
            continue
        try:
            res[inode] = _resolve_pid(pid, proc_root)
        except Exception:
            logger.debug("failed to resolve pid %s for inode %s", pid, inode)
            continue
    return res
