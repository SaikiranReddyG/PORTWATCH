from dataclasses import dataclass
from typing import List, Optional
from .proc import Socket, read_all
from .process import ProcessInfo, resolve_inodes


@dataclass(frozen=True)
class PortRecord:
    socket: Socket
    process: Optional[ProcessInfo]

    @property
    def protocol(self):
        return self.socket.protocol

    @property
    def local_ip(self):
        return self.socket.local_ip

    @property
    def local_port(self):
        return self.socket.local_port

    @property
    def remote_ip(self):
        return self.socket.remote_ip

    @property
    def remote_port(self):
        return self.socket.remote_port

    @property
    def state(self):
        return self.socket.state

    @property
    def pid(self):
        return self.process.pid if self.process else None

    @property
    def process_name(self):
        return self.process.name if self.process else "???"


def take_snapshot(proc_root: str = "/proc") -> List[PortRecord]:
    """Take a single snapshot: parse sockets and resolve processes in a single pass.

    Note: this builds the inode map once per call for efficiency.
    """
    socks = read_all(proc_root)
    inodes = {s.inode for s in socks if s.inode}
    inode_map = resolve_inodes(inodes, proc_root)
    records: List[PortRecord] = []
    for s in socks:
        p = inode_map.get(s.inode)
        records.append(PortRecord(socket=s, process=p))
    return records
