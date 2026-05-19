import argparse
import sys
from . import __version__
from .proc import read_all  # temporary debug command for Phase 1C


def main(argv=None):
    parser = argparse.ArgumentParser(prog="portwatch")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--dump", action="store_true", help="dump /proc/net/* sockets")
    args = parser.parse_args(argv)

    if args.version:
        print(f"portwatch {__version__}")
        return 0

    if args.dump:
        # Temporary debug output for Phase 1C: print one socket per line for all protocols
        socks = read_all()
        for s in socks:
            print(f"{s.protocol}  {s.local_ip}:{s.local_port}  {s.remote_ip}:{s.remote_port}  {s.state}  uid={s.uid}  inode={s.inode}")
        return 0

    print("not yet implemented — see PHASE files for build status")
    return 0
