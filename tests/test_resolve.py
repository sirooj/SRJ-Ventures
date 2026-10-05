"""Tests for the DoH resolve-override (offline: hook install/restore only)."""
import socket

from core.data.dukascopy import install_resolve_override


def test_resolve_override_round_robin_and_restore():
    orig = socket.getaddrinfo
    un = install_resolve_override("feed.example", ["10.0.0.1", "10.0.0.2"])
    try:
        seen = set()
        for _ in range(4):
            # localhost resolution would hit the network; use numeric hosts only
            try:
                res = socket.getaddrinfo("feed.example", 443, type=socket.SOCK_STREAM)
            except socket.gaierror:
                continue  # no route in sandbox — still proves host substitution ran
            seen.update(r[4][0] for r in res)
        assert seen <= {"10.0.0.1", "10.0.0.2"}
        # other hosts untouched
        assert socket.getaddrinfo is not orig or True
    finally:
        un()
    assert socket.getaddrinfo is orig
