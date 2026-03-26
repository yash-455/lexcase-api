from fastapi import HTTPException
from bson import ObjectId
from Models.hearing_model import HearingCreate, HearingUpdate
from DB.db_connect import hearing_collection, case_collection
from datetime import datetime, timezone


# add new hearing
async def add_hearing(hearing: HearingCreate):
    try:
        case = await case_collection.find_one({"_id": hearing.case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")

        hearing_document = {
            **hearing.dict(),
            "date": hearing.date,
            "created_at": datetime.now(timezone.utc)
        }

        result = await hearing_collection.insert_one(hearing_document)
        hearing_document["id"] = str(result.inserted_id)
        hearing_document.pop("_id", None)
        return hearing_document

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get all hearings — filter by upcoming/past, case_id, and user_id
async def get_hearings(filter: str = None, case_id: str = None, user_id: str = None):
    try:
        query = {}

        # ── Scope to user's cases only ──
        if user_id:
            user_cases = []
            async for case in case_collection.find({"user_id": user_id}, {"_id": 1}):
                user_cases.append(str(case["_id"]))
            if not user_cases:
                return []
            query["case_id"] = {"$in": user_cases}

        # override with specific case_id if provided (still must belong to user)
        if case_id:
            if user_id and case_id not in query.get("case_id", {}).get("$in", [case_id]):
                return []
            query["case_id"] = case_id

        # filter by upcoming or past
        now = datetime.now(timezone.utc)
        if filter == "upcoming":
            query["date"] = {"$gte": now}
        elif filter == "past":
            query["date"] = {"$lt": now}

        sort_order = 1 if filter == "upcoming" else -1

        cursor = hearing_collection.find(query).sort("date", sort_order)

        hearings = []
        async for hearing in cursor:
            hearing["id"] = str(hearing.pop("_id"))
            hearings.append(hearing)

        if not hearings:
            raise HTTPException(status_code=404, detail="No hearings found.")

        return hearings

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get single hearing by id
async def get_hearing(hearing_id: str):
    try:
        hearing = await hearing_collection.find_one({"_id": ObjectId(hearing_id)})
        if not hearing:
            raise HTTPException(status_code=404, detail="Hearing not found.")
        hearing["id"] = str(hearing.pop("_id"))
        return hearing
    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# update hearing by id
async def update_hearing(hearing_id: str, update_data: HearingUpdate, user_id: str):
    try:
        existing = await hearing_collection.find_one({"_id": ObjectId(hearing_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Hearing not found.")

        case = await case_collection.find_one({"_id": existing.get("case_id")})
        if not case or case.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized: You do not have permission to update this hearing.")

        fields_to_update = {
            key: value for key, value in update_data.dict().items() if value is not None
        }
        if not fields_to_update:
            return {"message": "No fields provided to update."}

        await hearing_collection.update_one(
            {"_id": ObjectId(hearing_id)},
            {"$set": fields_to_update}
        )
        return {"message": "Hearing updated successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# delete hearing by id
async def delete_hearing(hearing_id: str, user_id: str):
    try:
        existing = await hearing_collection.find_one({"_id": ObjectId(hearing_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Hearing not found.")

        case = await case_collection.find_one({"_id": existing.get("case_id")})
        if not case or case.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized: You do not have permission to delete this hearing.")

        await hearing_collection.delete_one({"_id": ObjectId(hearing_id)})
        return {"message": "Hearing deleted successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}