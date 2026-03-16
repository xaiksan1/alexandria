import uuid
from datetime import datetime, timezone, timedelta
from cache.models import BidCache, BidHistory, Sponsor, Base
from sqlalchemy import inspect


def test_bid_cache_tablename():
    assert BidCache.__tablename__ == "bid_cache"


def test_bid_history_tablename():
    assert BidHistory.__tablename__ == "bid_history"


def test_sponsor_tablename():
    assert Sponsor.__tablename__ == "sponsors"


def test_bid_cache_columns():
    mapper = inspect(BidCache)
    col_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "context_hash",
        "vertical",
        "encrypted_response",
        "hit_count",
        "win_count",
        "created_at",
        "last_hit_at",
        "expires_at",
    }
    assert required.issubset(col_names)


def test_bid_history_columns():
    mapper = inspect(BidHistory)
    col_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "bid_id",
        "context_hash",
        "vertical",
        "bid_amount",
        "w1",
        "w2",
        "won",
        "payment_confirmed",
        "revenue_credited",
        "created_at",
    }
    assert required.issubset(col_names)


def test_sponsor_columns():
    mapper = inspect(Sponsor)
    col_names = {c.key for c in mapper.columns}
    required = {
        "id",
        "vertical",
        "sponsor_name",
        "cta_type",
        "budget_remaining",
        "active",
        "created_at",
        "updated_at",
    }
    assert required.issubset(col_names)


def test_bid_cache_instantiation():
    entry = BidCache(
        context_hash="abc123",
        vertical="cloud",
        encrypted_response=b"encrypted_data",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    assert entry.context_hash == "abc123"
    assert entry.vertical == "cloud"


def test_bid_history_instantiation():
    record = BidHistory(
        bid_id=uuid.uuid4(),
        context_hash="abc",
        vertical="cloud",
        bid_amount=0.005,
    )
    assert record.bid_id is not None
    assert record.context_hash == "abc"
    assert record.vertical == "cloud"


def test_sponsor_instantiation():
    sponsor = Sponsor(
        vertical="crypto",
        sponsor_name="ACME Corp",
        cta_type="discover",
        budget_remaining=100.0,
    )
    assert sponsor.vertical == "crypto"
    assert sponsor.sponsor_name == "ACME Corp"
    assert sponsor.cta_type == "discover"
