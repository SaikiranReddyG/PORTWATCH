import time
import logging
from dataclasses import dataclass
from typing import List, Optional

from .snapshot import PortRecord, take_snapshot
from .diff import diff_snapshots, SnapshotDiff
from . import __version__

logger = logging.getLogger(__name__)


@dataclass
class SessionStats:
    start_time: float
    snapshot_count: int = 0
    peak_port_count: int = 0
    suspicious_count: int = 0
    parse_error_count: int = 0
    changes_detected: int = 0


def _timestr(ts: Optional[float] = None) -> str:
    t = time.localtime(ts if ts is not None else time.time())
    return time.strftime("%H:%M:%S", t)


def _format_baseline(snapshot: List[PortRecord], timestr: Optional[str] = None) -> str:
    listens = sum(1 for r in snapshot if r.state == "LISTEN")
    established = sum(1 for r in snapshot if r.state == "ESTABLISHED")
    other = len(snapshot) - listens - established
    return f"[{timestr or _timestr()}] baseline · {len(snapshot)} sockets ({listens} LISTEN, {established} ESTABLISHED, {other} other)"


def _format_change(kind: str, record: PortRecord, prev: Optional[PortRecord] = None, timestr: Optional[str] = None) -> str:
    ts = timestr or _timestr()
    s = record.socket
    proc = record.process
    if kind == "+":
        pname = proc.name if proc is not None else "???"
        pid = proc.pid if proc is not None else "-"
        return f"[{ts}] + {s.protocol}  {s.local_ip}:{s.local_port}  {s.state}  {pname} (pid={pid})"
    if kind == "-":
        pname = proc.name if proc is not None else "???"
        pid = proc.pid if proc is not None else "-"
        return f"[{ts}] - {s.protocol}  {s.local_ip}:{s.local_port}  {s.state}  {pname} (pid={pid})"
    # changed
    prev_state = prev.state if prev is not None else "?"
    prev_proc = prev.process if prev is not None else None
    prev_name = prev_proc.name if prev_proc is not None else "???"
    prev_pid = prev_proc.pid if prev_proc is not None else "-"
    curr_name = proc.name if proc is not None else "???"
    curr_pid = proc.pid if proc is not None else "-"
    pname_bit = f"{prev_name}→{curr_name}" if prev_name != curr_name else curr_name
    return f"[{ts}] ~ {s.protocol}  {s.local_ip}:{s.local_port}  {prev_state}→{s.state}  {pname_bit} (pid={prev_pid}→pid={curr_pid})"


def _format_runtime(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    mins, sec = divmod(seconds, 60)
    if mins < 60:
        return f"{mins}m {sec}s"
    hrs, m = divmod(mins, 60)
    return f"{hrs}h {m}m {sec}s"


def _format_summary(stats: SessionStats, runtime_seconds: Optional[int] = None) -> str:
    now = int(time.time())
    runtime = runtime_seconds if runtime_seconds is not None else int(now - stats.start_time)
    rt = _format_runtime(runtime)
    lines = ["───────────────────────────────────", "portwatch session summary"]
    lines.append(f"  runtime     : {rt}")
    lines.append(f"  snapshots   : {stats.snapshot_count}")
    lines.append(f"  peak ports  : {stats.peak_port_count}")
    lines.append(f"  changes     : {stats.changes_detected}")
    lines.append(f"  suspicious  : {stats.suspicious_count}")
    lines.append(f"  parse errors: {stats.parse_error_count}")
    lines.append("───────────────────────────────────")
    return "\n".join(lines)


def run_loop(poll_interval: float = 2.0, proc_root: str = "/proc") -> SessionStats:
    stats = SessionStats(start_time=time.time())
    print(f"portwatch v{__version__} · polling every {poll_interval}s · press Ctrl+C to stop")

    previous: List[PortRecord] = []
    consecutive_failures = 0

    try:
        snapshot = take_snapshot(proc_root)
        stats.snapshot_count = 1
        stats.peak_port_count = len(snapshot)
        print(_format_baseline(snapshot))
        previous = snapshot
    except Exception:
        logger.exception("failed to take initial snapshot")
        stats.parse_error_count += 1

    while True:
        try:
            time.sleep(poll_interval)
            snapshot = take_snapshot(proc_root)
            stats.snapshot_count += 1
            stats.peak_port_count = max(stats.peak_port_count, len(snapshot))
            diff: SnapshotDiff = diff_snapshots(previous, snapshot)
            if diff.is_empty:
                consecutive_failures = 0
                previous = snapshot
                continue
            # print changes
            ts = _timestr()
            for r in diff.added:
                print(_format_change("+", r, None, ts))
            for r in diff.removed:
                print(_format_change("-", r, None, ts))
            for prev_r, curr_r in diff.changed:
                print(_format_change("~", curr_r, prev_r, ts))
            stats.changes_detected += len(diff.added) + len(diff.removed) + len(diff.changed)
            consecutive_failures = 0
            previous = snapshot
        except KeyboardInterrupt:
            print("\n", _format_summary(stats))
            return stats
        except Exception:
            logger.exception("error during polling tick")
            stats.parse_error_count += 1
            consecutive_failures += 1
            if consecutive_failures >= 10:
                print("Too many consecutive failures; exiting.")
                print(_format_summary(stats))
                return stats
            # sleep then continue
            time.sleep(poll_interval)
            continue
