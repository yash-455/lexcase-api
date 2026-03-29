from datetime import datetime, timezone
from fastapi import HTTPException
from DB.db_connect import case_collection, hearing_collection, doc_collection, chat_collection


def _to_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            # Supports "2026-03-28T10:20:30Z" and standard ISO strings.
            if value.endswith("Z"):
                value = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _iso(value):
    dt = _to_datetime(value)
    return dt.isoformat() if dt else None


async def get_dashboard_stats(user_id: str):
    try:
        # Cases for this user.
        cases = []
        async for c in case_collection.find({"user_id": user_id}):
            cases.append(c)

        case_ids = [str(c.get("_id")) for c in cases]

        active_cases = sum(
            1
            for c in cases
            if str(c.get("status", "")).lower() != "closed"
        )

        now = datetime.now(timezone.utc)

        upcoming_hearings = 0
        if case_ids:
            upcoming_hearings = await hearing_collection.count_documents({
                "case_id": {"$in": case_ids},
                "$or": [
                    {"next_date": {"$gte": now}},
                    {"date": {"$gte": now}},
                ],
            })

        # Documents are in sync collection.
        pending_documents = doc_collection.count_documents({
            "filename": {"$exists": True},
            "user_id": user_id,
        })

        # Chat collection is async.
        ai_queries = await chat_collection.count_documents({"user_id": user_id})

        return {
            "active_cases": active_cases,
            "upcoming_hearings": upcoming_hearings,
            "pending_documents": pending_documents,
            "ai_queries": ai_queries,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_recent_activity(user_id: str, limit: int = 10):
    try:
        # Build case map once.
        cases = []
        case_name_map = {}
        async for c in case_collection.find({"user_id": user_id}):
            cid = str(c.get("_id"))
            cases.append(c)
            case_name_map[cid] = c.get("case_name") or c.get("case_number") or f"Case {cid}"

        case_ids = [str(c.get("_id")) for c in cases]

        events = []

        # Case events.
        for c in cases:
            cid = str(c.get("_id"))
            created_at = _to_datetime(c.get("created_at"))
            updated_at = _to_datetime(c.get("updated_at"))

            if created_at:
                events.append({
                    "id": f"case-created-{cid}",
                    "type": "Case",
                    "case_id": cid,
                    "case_name": case_name_map.get(cid),
                    "action": "Case created",
                    "status": "completed",
                    "date": created_at,
                })

            has_meaningful_update = False
            if updated_at and created_at:
                has_meaningful_update = abs((updated_at - created_at).total_seconds()) > 1
            elif updated_at and not created_at:
                has_meaningful_update = True

            if has_meaningful_update:
                events.append({
                    "id": f"case-updated-{cid}",
                    "type": "Case",
                    "case_id": cid,
                    "case_name": case_name_map.get(cid),
                    "action": f"Case status: {c.get('status', 'updated')}",
                    "status": "completed" if str(c.get("status", "")).lower() == "closed" else "upcoming",
                    "date": updated_at,
                })

        # Hearing events.
        if case_ids:
            hearing_cursor = hearing_collection.find({"case_id": {"$in": case_ids}}).sort("created_at", -1).limit(limit * 5)

            async for h in hearing_cursor:
                hid = str(h.get("_id"))
                event_dt = _to_datetime(h.get("updated_at")) or _to_datetime(h.get("created_at")) or _to_datetime(h.get("date"))
                if not event_dt:
                    continue

                hearing_dt = _to_datetime(h.get("next_date")) or _to_datetime(h.get("date"))
                if h.get("outcome"):
                    status = "completed"
                else:
                    status = "completed" if hearing_dt and hearing_dt < datetime.now(timezone.utc) else "upcoming"

                case_id = h.get("case_id")
                events.append({
                    "id": f"hearing-{hid}",
                    "type": "Hearing",
                    "case_id": case_id,
                    "case_name": case_name_map.get(case_id, f"Case {case_id}"),
                    "action": f"Hearing outcome: {h.get('outcome')}" if h.get("outcome") else "Hearing scheduled",
                    "status": status,
                    "date": event_dt,
                })

        # Document events (sync cursor).
        if case_ids:
            doc_cursor = doc_collection.find({
                "filename": {"$exists": True},
                "user_id": user_id,
                "case_id": {"$in": case_ids},
            }).sort("uploaded_at", -1).limit(limit * 3)

            for d in doc_cursor:
                dt = _to_datetime(d.get("uploaded_at"))
                if not dt:
                    continue

                did = d.get("doc_id") or str(d.get("_id"))
                case_id = d.get("case_id")

                events.append({
                    "id": f"doc-{did}",
                    "type": "Document",
                    "case_id": case_id,
                    "case_name": case_name_map.get(case_id, f"Case {case_id}"),
                    "action": "Document uploaded",
                    "status": "completed",
                    "date": dt,
                })

        # Latest N.
        events.sort(key=lambda x: x["date"], reverse=True)
        events = events[:limit]

        # Convert date to ISO for JSON.
        for e in events:
            e["date"] = _iso(e["date"])

        return events

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))