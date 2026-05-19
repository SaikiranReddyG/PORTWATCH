from dataclasses import dataclass
import logging
from typing import List, Tuple, Callable
import ipaddress

logger = logging.getLogger(__name__)

# Mapping of hex state codes from /proc/net/* to human-readable names
STATE_MAP = {
    "01": "ESTABLISHED",
    "02": "SYN_SENT",
    "03": "SYN_RECV",
    "04": "FIN_WAIT1",
    "05": "FIN_WAIT2",
    "06": "TIME_WAIT",
    "07": "CLOSE",
    "08": "CLOSE_WAIT",
    "09": "LAST_ACK",
    "0A": "LISTEN",
    "0B": "CLOSING",
    "0C": "NEW_SYN_RECV",
}


@dataclass(frozen=True)
class Socket:
    """A parsed socket row from `/proc/net/*`.

    Fields are intentionally primitive to keep this phase focused on parsing.
    """

    protocol: str
    local_ip: str
    local_port: int
    remote_ip: str
    remote_port: int
    state: str
    inode: int
    uid: int


# Convert a token like "AABBCCDD:PPPP" into (ip_str, port_int).
def _parse_addr(token: str) -> Tuple[str, int]:
    ip_hex, port_hex = token.split(":")
    # ip_hex is little-endian, convert to bytes and reverse
    b = bytes.fromhex(ip_hex)
    ip_bytes = b[::-1]
    ip_str = ".".join(str(x) for x in ip_bytes)
    port = int(port_hex, 16)
    return ip_str, port


# Convert a 32-char IPv6 hex token like "AAAAAAAA...:PPPP" into (ip_str, port_int).
def _parse_addr6(token: str) -> Tuple[str, int]:
    # token form: 32-hexchars:PORT
    ip_hex, port_hex = token.split(":")
    if len(ip_hex) != 32:
        raise ValueError("invalid ipv6 hex length")
    # each 8 chars is a 4-byte group; groups are in network order, bytes within group are little-endian
    groups = [ip_hex[i : i + 8] for i in range(0, 32, 8)]
    parts = []
    for g in groups:
        gb = bytes.fromhex(g)
        parts.append(gb[::-1])
    ip_bytes = b"".join(parts)
    ip_addr = ipaddress.IPv6Address(ip_bytes)
    return str(ip_addr), int(port_hex, 16)


def _parse_proc_net(path: str, protocol: str, addr_parser: Callable[[str], Tuple[str, int]]) -> List[Socket]:
    sockets: List[Socket] = []

    with open(path, "r", encoding="utf8") as fh:
        # skip header
        fh.readline()
        for lineno, line in enumerate(fh, start=2):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 10:
                logger.warning("malformed %s line %d: %r", path, lineno, line)
                continue

            try:
                local_tok = parts[1]
                remote_tok = parts[2]
                state_code = parts[3].upper()
                uid = int(parts[7])
                inode = int(parts[9])

                local_ip, local_port = addr_parser(local_tok)
                remote_ip, remote_port = addr_parser(remote_tok)

                state = STATE_MAP.get(state_code, "UNKNOWN")
                if state == "UNKNOWN":
                    logger.warning("unknown state code %r on line %d", state_code, lineno)

                sock = Socket(
                    protocol=protocol,
                    local_ip=local_ip,
                    local_port=local_port,
                    remote_ip=remote_ip,
                    remote_port=remote_port,
                    state=state,
                    inode=inode,
                    uid=uid,
                )
                sockets.append(sock)
            except Exception:
                logger.warning("failed to parse %s line %d: %r", path, lineno, line)
                continue

    return sockets


def read_tcp4(path: str = "/proc/net/tcp") -> List[Socket]:
    return _parse_proc_net(path, "tcp4", _parse_addr)


def read_tcp6(path: str = "/proc/net/tcp6") -> List[Socket]:
    return _parse_proc_net(path, "tcp6", _parse_addr6)


def read_udp4(path: str = "/proc/net/udp") -> List[Socket]:
    return _parse_proc_net(path, "udp4", _parse_addr)


def read_udp6(path: str = "/proc/net/udp6") -> List[Socket]:
    return _parse_proc_net(path, "udp6", _parse_addr6)


def read_all() -> List[Socket]:
    results: List[Socket] = []
    for fn, proto_fn in (
        ("/proc/net/tcp", read_tcp4),
        ("/proc/net/tcp6", read_tcp6),
        ("/proc/net/udp", read_udp4),
        ("/proc/net/udp6", read_udp6),
    ):
        try:
            results.extend(proto_fn(fn))
        except FileNotFoundError:
            logger.warning("%s not found; skipping %s", fn, proto_fn.__name__)
            continue
    return results
