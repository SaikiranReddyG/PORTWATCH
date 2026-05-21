from dataclasses import dataclass
from typing import List, Tuple

from .snapshot import PortRecord


def _record_key(record: PortRecord) -> tuple:
    """Identity key for a PortRecord.

    Note: If multiple records in a single snapshot share the same identity key
    (same protocol + local ip + local port), the last one wins when building
    the dicts used by `diff_snapshots`. Multi-connection tracking per local
    port is out of scope for PHASE_1F.
    """
    return (record.protocol, record.local_ip, record.local_port)


@dataclass(frozen=True)
class SnapshotDiff:
    added: List[PortRecord]
    removed: List[PortRecord]
    changed: List[Tuple[PortRecord, PortRecord]]

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


def _has_changed(prev: PortRecord, curr: PortRecord) -> bool:
    """Return True if any observable property (besides uid) changed.

    Changes considered:
    - state
    - remote_ip
    - remote_port
    - process_name
    - pid
    """
    if prev.state != curr.state:
        return True
    if prev.remote_ip != curr.remote_ip:
        return True
    if prev.remote_port != curr.remote_port:
        return True
    if prev.process_name != curr.process_name:
        return True
    # pid may be None; consider difference as change
    if prev.pid != curr.pid:
        return True
    return False


def diff_snapshots(previous: List[PortRecord], current: List[PortRecord]) -> SnapshotDiff:
    """Compute a SnapshotDiff between two lists of PortRecord.

    Implementation notes:
    - Uses `_record_key` as the identity key.
    - If duplicate keys exist within a snapshot, the last record wins.
    """
    prev_map = { _record_key(r): r for r in previous }
    curr_map = { _record_key(r): r for r in current }

    added = [r for k, r in curr_map.items() if k not in prev_map]
    removed = [r for k, r in prev_map.items() if k not in curr_map]

    changed: List[Tuple[PortRecord, PortRecord]] = []
    for k in (set(prev_map.keys()) & set(curr_map.keys())):
        p = prev_map[k]
        c = curr_map[k]
        if _has_changed(p, c):
            changed.append((p, c))

    return SnapshotDiff(added=added, removed=removed, changed=changed)
