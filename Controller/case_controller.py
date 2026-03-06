from fastapi import HTTPException
from bson import ObjectId
from Models.case_model import CaseCreate, CaseResponse, CaseUpdate, CaseStatus
from DB.mongo import case_collection
from datetime import datetime, timezone
from typing import Optional
import uuid


# add new case
async def add_case(case: CaseCreate, user_id: str):
    try:
        # check if case number already exists
        existing = await case_collection.find_one({"case_number": case.case_number})
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Case with number '{case.case_number}' already exists."
            )

        now = datetime.now(timezone.utc)

        case_document = {
            "_id": str(uuid.uuid4()),
            **case.dict(),
            "user_id": user_id,             # ✅ which lawyer created this case
            "ai_summary": None,
            "created_at": now,
            "updated_at": now,
        }

        await case_collection.insert_one(case_document)

        case_document["id"] = case_document.pop("_id")
        return CaseResponse(**case_document)

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get all cases — search by case_name or case_number, filter by status
async def get_cases_search(
    name: Optional[str] = None,
    status: Optional[CaseStatus] = None,
    user_id: str = None
):
    try:
        query = {}

        # filter by logged in lawyer
        if user_id:
            query["user_id"] = user_id

        # search by case_name or case_number (partial, case-insensitive)
        if name:
            query["$or"] = [
                {"case_name": {"$regex": name, "$options": "i"}},
                {"case_number": {"$regex": name, "$options": "i"}}
            ]

        # filter by status
        if status:
            query["status"] = status.value

        cursor = case_collection.find(query)

        cases = []
        async for case in cursor:
            case["id"] = str(case.pop("_id"))
            cases.append(case)

        if not cases:
            raise HTTPException(
                status_code=404,
                detail="No cases found."
            )

        return cases

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get single case by id
async def get_case(case_id: str):
    try:
        case = await case_collection.find_one({"_id": case_id})
        if not case:
            raise HTTPException(
                status_code=404,
                detail=f"Case not found."
            )

        case["id"] = str(case.pop("_id"))
        return case

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# update case by id
async def update_case(case_id: str, update_data: CaseUpdate):
    try:
        existing = await case_collection.find_one({"_id": case_id})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Case not found."
            )

        fields_to_update = {
            key: value
            for key, value in update_data.dict().items()
            if value is not None
        }

        if not fields_to_update:
            return {"message": "No fields provided to update."}

        fields_to_update["updated_at"] = datetime.now(timezone.utc)

        await case_collection.update_one(
            {"_id": case_id},
            {"$set": fields_to_update}
        )

        return {"message": "Case updated successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# delete case by id
async def delete_case(case_id: str):
    try:
        existing = await case_collection.find_one({"_id": case_id})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Case not found."
            )

        await case_collection.delete_one({"_id": case_id})
        return {"message": "Case deleted successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}