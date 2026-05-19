from pathlib import Path
import logging
import pytest

from portwatch.proc import read_tcp4, Socket


FIXTURES = Path(__file__).parent / "fixtures"


def test_empty_file_returns_empty_list():
    path = FIXTURES / "proc_net_tcp_empty.txt"
    assert read_tcp4(str(path)) == []


def test_basic_parses_listen_and_established():
    path = FIXTURES / "proc_net_tcp_basic.txt"
    socks = read_tcp4(str(path))
    assert len(socks) == 2
    listen, est = socks
    assert listen.protocol == "tcp4"
    assert listen.local_ip == "0.0.0.0"
    assert listen.local_port == 22
    assert listen.remote_ip == "0.0.0.0"
    assert listen.remote_port == 0
    assert listen.state == "LISTEN"
    assert listen.uid == 1000
    assert listen.inode == 12345

    assert est.local_ip == "127.0.0.1"
    assert est.local_port == 8080
    assert est.remote_ip == "192.168.1.10"
    assert est.remote_port == 443
    assert est.state == "ESTABLISHED"


def test_mixed_states_are_all_recognised():
    path = FIXTURES / "proc_net_tcp_mixed.txt"
    socks = read_tcp4(str(path))
    states = [s.state for s in socks]
    assert "LISTEN" in states
    assert "ESTABLISHED" in states
    assert "TIME_WAIT" in states


def test_listen_socket_has_zero_remote_port():
    path = FIXTURES / "proc_net_tcp_basic.txt"
    socks = read_tcp4(str(path))
    listen = socks[0]
    assert listen.remote_port == 0
    assert listen.remote_ip == "0.0.0.0"


def test_malformed_rows_are_skipped_not_raised(caplog):
    caplog.set_level(logging.WARNING)
    path = FIXTURES / "proc_net_tcp_malformed.txt"
    socks = read_tcp4(str(path))
    # three valid rows expected
    assert len(socks) == 3
    # two warnings for malformed rows
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) >= 2


def test_unknown_state_code_yields_unknown_string(caplog, tmp_path):
    caplog.set_level(logging.WARNING)
    p = tmp_path / "one_unknown.txt"
    p.write_text(
        "sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
        "  0: 0100007F:1F90 00000000:0000 FF 00000000:00000000 00:00000000 00000000   1000        0 99999 1 0000000000000000 100 0 0 10 0\n"
    )
    socks = read_tcp4(str(p))
    assert len(socks) == 1
    assert socks[0].state == "UNKNOWN"
    assert any("unknown state code" in r.getMessage() for r in caplog.records)


def test_missing_file_raises_filenotfound(caplog):
    caplog.set_level(logging.WARNING)
    with pytest.raises(FileNotFoundError):
        read_tcp4("/nonexistent/path/for_tests/net_tcp")
    # no warnings should be logged for missing file
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def test_tcp6_basic_parses_listen_and_established():
    path = FIXTURES / "proc_net_tcp6_basic.txt"
    from portwatch.proc import read_tcp6

    socks = read_tcp6(str(path))
    assert len(socks) == 2
    listen, est = socks
    assert listen.protocol == "tcp6"
    assert listen.local_ip == "::1"
    assert listen.local_port == 22
    assert listen.remote_ip == "::"
    assert listen.remote_port == 0
    assert listen.state == "LISTEN"

    assert est.protocol == "tcp6"
    assert est.state == "ESTABLISHED"


def test_tcp6_loopback_is_compressed():
    path = FIXTURES / "proc_net_tcp6_basic.txt"
    from portwatch.proc import read_tcp6
    socks = read_tcp6(str(path))
    assert socks[0].local_ip == "::1"


def test_tcp6_malformed_rows_skipped(caplog):
    caplog.set_level(logging.WARNING)
    path = FIXTURES / "proc_net_tcp6_malformed.txt"
    from portwatch.proc import read_tcp6
    socks = read_tcp6(str(path))
    assert len(socks) == 2
    assert any("malformed" in r.getMessage() or "failed to parse" in r.getMessage() for r in caplog.records)


def test_udp4_basic_parses_close_and_established():
    path = FIXTURES / "proc_net_udp_basic.txt"
    from portwatch.proc import read_udp4
    socks = read_udp4(str(path))
    assert len(socks) == 2
    states = [s.state for s in socks]
    assert "CLOSE" in states
    assert "ESTABLISHED" in states
    assert all(s.protocol == "udp4" for s in socks)


def test_udp4_close_state_is_07():
    path = FIXTURES / "proc_net_udp_basic.txt"
    from portwatch.proc import read_udp4
    socks = read_udp4(str(path))
    close = [s for s in socks if s.state == "CLOSE"]
    assert len(close) == 1


def test_udp6_basic_parses_sockets():
    path = FIXTURES / "proc_net_udp6_basic.txt"
    from portwatch.proc import read_udp6
    socks = read_udp6(str(path))
    assert len(socks) == 2
    assert all(s.protocol == "udp6" for s in socks)


def test_read_all_combines_all_protocols(monkeypatch):
    import portwatch.proc as proc
    from portwatch.proc import read_tcp4, read_tcp6, read_udp4, read_udp6

    # patch each reader to use fixture paths
    monkeypatch.setattr(proc, 'read_tcp4', lambda p=None: read_tcp4(str(FIXTURES / "proc_net_tcp_basic.txt")))
    monkeypatch.setattr(proc, 'read_tcp6', lambda p=None: read_tcp6(str(FIXTURES / "proc_net_tcp6_basic.txt")))
    monkeypatch.setattr(proc, 'read_udp4', lambda p=None: read_udp4(str(FIXTURES / "proc_net_udp_basic.txt")))
    monkeypatch.setattr(proc, 'read_udp6', lambda p=None: read_udp6(str(FIXTURES / "proc_net_udp6_basic.txt")))

    all_socks = proc.read_all()
    protos = set(s.protocol for s in all_socks)
    assert protos >= {"tcp4", "tcp6", "udp4", "udp6"}


def test_read_all_survives_missing_file(monkeypatch, caplog):
    import portwatch.proc as proc
    caplog.set_level(logging.WARNING)

    # make tcp6 raise FileNotFoundError
    original_tcp6 = proc.read_tcp6
    def missing_tcp6(p=None):
        raise FileNotFoundError()

    monkeypatch.setattr(proc, 'read_tcp6', missing_tcp6)
    from portwatch.proc import read_tcp4, read_udp4, read_udp6
    # let others point to fixtures
    monkeypatch.setattr(proc, 'read_tcp4', lambda p=None: read_tcp4(str(FIXTURES / "proc_net_tcp_basic.txt")))
    monkeypatch.setattr(proc, 'read_udp4', lambda p=None: read_udp4(str(FIXTURES / "proc_net_udp_basic.txt")))
    monkeypatch.setattr(proc, 'read_udp6', lambda p=None: read_udp6(str(FIXTURES / "proc_net_udp6_basic.txt")))

    all_socks = proc.read_all()
    # tcp6 missing should have produced a warning
    assert any("not found; skipping" in r.getMessage() or "not found" in r.getMessage() for r in caplog.records)
    protos = set(s.protocol for s in all_socks)
    assert "tcp6" not in protos
    assert protos & {"tcp4", "udp4", "udp6"}
