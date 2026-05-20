import argparse
import sys
import logging
from . import __version__
from .snapshot import take_snapshot
from .loop import run_loop
from .app import run_tui


def main(argv=None):
    parser = argparse.ArgumentParser(prog="portwatch")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--dump", action="store_true", help="dump /proc/net/* sockets")
    parser.add_argument("--interval", type=float, default=2.0, help="poll interval in seconds")
    parser.add_argument("--verbose", action="store_true", help="enable debug logging on stderr")
    parser.add_argument("--tui", action="store_true", help="launch the Textual TUI")
    args = parser.parse_args(argv)

    # configure logging
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

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

    if args.tui:
        try:
            run_tui()
        except Exception as e:
            logging.exception("TUI failed to start")
            print("error: could not start TUI (is textual installed?)", file=sys.stderr)
            return 1
        return 0

    # Validate interval
    if args.interval <= 0:
        print("error: --interval must be positive", file=sys.stderr)
        return 2

    # Run live loop
    try:
        run_loop(poll_interval=args.interval)
    except Exception:
        logging.exception("fatal error running loop")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
