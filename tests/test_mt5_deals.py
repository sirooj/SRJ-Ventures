"""Tests for MT5 deal-tape → trade-list netting (fixture)."""
from datetime import datetime, timezone

from core.propfirm.mt5_deals import deals_to_trades

UTC = timezone.utc


def _d(minute, side, vol, price, symbol="EURUSD"):
    return {"time": datetime(2026, 3, 2, 10, minute, tzinfo=UTC),
            "symbol": symbol, "side": side, "volume": vol, "price": price}


def test_fifo_partial_and_flip():
    deals = [
        _d(0, 1, 2.0, 1.1000),    # buy 2.0
        _d(5, -1, 1.0, 1.1020),   # sell 1.0 → closes half: +20/unit
        _d(10, -1, 2.0, 1.1010),  # sell 2.0 → closes rest (+10) + flips short 1.0
        _d(15, 1, 1.0, 1.0990),   # buy 1.0 → closes short (+20)
    ]
    trades = deals_to_trades(deals)
    assert len(trades) == 3
    assert [t["side"] for t in trades] == [1, 1, -1]
    assert [t["size"] for t in trades] == [1.0, 1.0, 1.0]
    assert trades[0]["entry_price"] == 1.1000 and trades[0]["exit_price"] == 1.1020
    assert trades[1]["exit_price"] == 1.1010
    assert trades[2]["entry_price"] == 1.1010 and trades[2]["exit_price"] == 1.0990
    # P/L: +20 +10 +20 = +50 (multiplier 1)
    pnl = sum(t["side"] * (t["exit_price"] - t["entry_price"]) * t["size"]
              for t in trades)
    assert abs(pnl - 0.0050) < 1e-9


def test_per_symbol_netting():
    deals = [_d(0, 1, 1.0, 1.1), _d(1, 1, 1.0, 150.0, "USDJPY"),
             _d(2, -1, 1.0, 1.2), _d(3, -1, 1.0, 151.0, "USDJPY")]
    trades = deals_to_trades(deals)
    assert {t["symbol"] for t in trades} == {"EURUSD", "USDJPY"}
    assert len(trades) == 2
