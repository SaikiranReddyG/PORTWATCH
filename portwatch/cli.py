import argparse
import sys
from . import __version__
from .snapshot import take_snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(prog="portwatch")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--dump", action="store_true", help="dump /proc/net/* sockets")
    args = parser.parse_args(argv)

    if args.version:
        print(f"portwatch {__version__}")
        return 0

    if args.dump:
        # Use snapshot builder to get combined socket+process records
        records = take_snapshot()
        for r in records:
            s = r.socket
            p = r.process
            if p is not None:
                proc_part = f"{p.name} (pid={p.pid}, {p.exe})  uid={s.uid}({p.username})"
            else:
                proc_part = f"??? (pid=-, inode={s.inode})  uid={s.uid}"
            print(f"{s.protocol}  {s.local_ip}:{s.local_port}  {s.remote_ip}:{s.remote_port}  {s.state}  {proc_part}")
        return 0

    print("not yet implemented — see PHASE files for build status")
    return 0
