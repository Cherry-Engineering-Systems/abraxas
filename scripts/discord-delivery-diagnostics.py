#!/usr/bin/env python3
"""
discord-delivery-diagnostics.py — Track and diagnose Discord message delivery issues.

Writes to ArangoDB message_log collection, analyzes gaps in delivery chains.
"""

import datetime
import json
import os
import sys
from typing import Optional

from arango import ArangoClient

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def _get_db():
    url = os.environ.get("ARANGO_URL", "http://localhost:8529")
    db_name = os.environ.get("ARANGO_DB", "abraxas_db")
    user = os.environ.get("ARANGO_USER", "root")
    pw = os.environ.get("ARANGO_ROOT_PASSWORD", "TheBestPassword!")
    client = ArangoClient(hosts=url)
    return client.db(db_name, username=user, password=pw)


# ---------------------------------------------------------------------------
# Message logging
# ---------------------------------------------------------------------------

def log_message(
    message_id: str,
    channel_id: str,
    session_id: str,
    content_preview: str,
    content_length: int,
    message_count_in_session: int,
    delivery_method: str = "discord",
    expected_delivery: bool = True,
    sender: str = "mary-jane",
    metadata: Optional[dict] = None,
) -> str:
    """Log a message send event to the message_log collection for delivery tracking."""
    db = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    doc = {
        "message_id": message_id,
        "channel_id": channel_id,
        "session_id": session_id,
        "content_preview": content_preview[:200],
        "content_length": content_length,
        "message_count_in_session": message_count_in_session,
        "delivery_method": delivery_method,
        "expected_delivery": expected_delivery,
        "delivered": None,  # Updated when confirmed
        "sender": sender,
        "timestamp_utc": now,
        "metadata": metadata or {},
    }
    result = db.collection("message_log").insert(doc)
    return result["_key"]


def confirm_delivery(message_id: str, confirmed: bool = True):
    """Mark a previously logged message as delivered (or not)."""
    db = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    cursor = db.aql.execute(
        """
        FOR m IN message_log
        FILTER m.message_id == @msg_id
        UPDATE m WITH { delivered: @status, confirmed_at: @now } IN message_log
        RETURN NEW._key
        """,
        bind_vars={"msg_id": message_id, "status": confirmed, "now": now},
    )
    results = list(cursor)
    return len(results)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def analyze_session(session_id: str) -> dict:
    """Analyze a session for delivery gaps.

    Returns: dict with gap count, gap details, delivery rate.
    """
    db = _get_db()

    cursor = db.aql.execute(
        """
        FOR m IN message_log
        FILTER m.session_id == @sid AND m.sender == 'mary-jane'
        SORT m.timestamp_utc
        RETURN m
        """,
        bind_vars={"sid": session_id},
    )
    messages = list(cursor)

    if not messages:
        return {"error": "No messages for this session", "message_count": 0}

    sent_count = len(messages)
    confirmed_count = sum(1 for m in messages if m.get("delivered") is True)
    missing_count = sum(1 for m in messages if m.get("delivered") is False)
    unknown_count = sum(1 for m in messages if m.get("delivered") is None)
    delivery_rate = (confirmed_count / sent_count) * 100 if sent_count > 0 else 0

    # Find gaps — consecutive messages > 1 second apart where one has content_length > 1800
    # (could indicate a split message that lost the tail)
    gaps = []
    for i in range(1, len(messages)):
        prev = messages[i - 1]
        curr = messages[i]
        prev_ts = datetime.datetime.fromisoformat(prev["timestamp_utc"])
        curr_ts = datetime.datetime.fromisoformat(curr["timestamp_utc"])
        delta_ms = (curr_ts - prev_ts).total_seconds() * 1000

        if prev.get("content_length", 0) > 1800 and delta_ms < 500:
            # Message was likely split for Discord — check if this is the continuation
            if (
                prev.get("delivered") is None
                and curr.get("delivered") is not False
            ):
                gaps.append(
                    {
                        "type": "possible_split_loss",
                        "message_id": prev["message_id"],
                        "content_preview": prev.get("content_preview", "")[:80],
                        "content_length": prev.get("content_length", 0),
                        "next_message_id": curr["message_id"],
                        "gap_ms": delta_ms,
                        "note": "Long message followed by short gap — tail may be lost",
                    }
                )

        if prev.get("delivered") is None and delta_ms > 30000:
            gaps.append(
                {
                    "type": "long_silence_after_unconfirmed",
                    "message_id": prev["message_id"],
                    "content_preview": prev.get("content_preview", "")[:80],
                    "gap_seconds": delta_ms / 1000,
                    "note": "Unconfirmed message followed by 30s+ gap",
                }
            )

    # Detect burst patterns (many messages in < 2 seconds = rate limit risk)
    bursts = []
    burst_start = None
    burst_count = 0
    for i, m in enumerate(messages):
        if i == 0:
            continue
        prev_ts = datetime.datetime.fromisoformat(messages[i - 1]["timestamp_utc"])
        curr_ts = datetime.datetime.fromisoformat(m["timestamp_utc"])
        delta_ms = (curr_ts - prev_ts).total_seconds() * 1000

        if delta_ms < 2000:
            if burst_start is None:
                burst_start = i - 1
            burst_count += 1
        else:
            if burst_count >= 3:
                start_msg = messages[burst_start]
                bursts.append(
                    {
                        "start_message_id": start_msg["message_id"],
                        "count": burst_count,
                        "timeframe_ms": delta_ms,
                        "note": "Burst of messages — possible rate limit trigger",
                    }
                )
            burst_start = None
            burst_count = 0

    return {
        "session_id": session_id,
        "message_count": sent_count,
        "confirmed": confirmed_count,
        "missing": missing_count,
        "unknown": unknown_count,
        "delivery_rate_pct": round(delivery_rate, 1),
        "gaps": gaps,
        "gaps_count": len(gaps),
        "bursts": bursts,
        "bursts_count": len(bursts),
    }


def recent_delivery_health(hours: int = 24) -> dict:
    """Get delivery health stats for the last N hours."""
    db = _get_db()
    since = (
        datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(hours=hours)
    ).isoformat()

    cursor = db.aql.execute(
        """
        FOR m IN message_log
        FILTER m.timestamp_utc >= @since AND m.sender == 'mary-jane'
        COLLECT channel = m.channel_id INTO group
        LET total = LENGTH(group)
        LET confirmed = LENGTH(FOR g IN group FILTER g.m.delivered == true RETURN 1)
        LET missing = LENGTH(FOR g IN group FILTER g.m.delivered == false RETURN 1)
        LET unknown = LENGTH(FOR g IN group FILTER g.m.delivered == null RETURN 1)
        SORT total DESC
        RETURN {
            channel_id: channel,
            total: total,
            confirmed: confirmed,
            missing: missing,
            unknown: unknown,
            rate: ROUND(confirmed / total * 100, 1)
        }
        """,
        bind_vars={"since": since},
    )
    return list(cursor)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: discord-delivery-diagnostics.py <action> [args...]")
        print()
        print("Actions:")
        print("  log <message_id> <channel_id> <session_id> <preview> <length> <count>")
        print("  confirm <message_id> [true|false]")
        print("  analyze <session_id>")
        print("  health [hours=24]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "log":
        mid, cid, sid, preview, length, count = sys.argv[2:8]
        key = log_message(
            message_id=mid,
            channel_id=cid,
            session_id=sid,
            content_preview=preview,
            content_length=int(length),
            message_count_in_session=int(count),
        )
        print(f"Logged: {key}")

    elif action == "confirm":
        mid = sys.argv[2]
        confirmed = sys.argv[3].lower() != "false" if len(sys.argv) > 3 else True
        count = confirm_delivery(mid, confirmed)
        print(f"Updated {count} record(s) for {mid} → delivered={confirmed}")

    elif action == "analyze":
        sid = sys.argv[2]
        result = analyze_session(sid)
        print(json.dumps(result, indent=2, default=str))

    elif action == "health":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        result = recent_delivery_health(hours)
        print(json.dumps(result, indent=2, default=str))

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
