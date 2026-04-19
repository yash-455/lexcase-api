from fastapi import HTTPException
from bson import ObjectId
from Models.case_model import CaseCreate, CaseResponse, CaseUpdate, CaseStatus
from DB.db_connect import case_collection
from datetime import datetime, timezone
from typing import Optional
import uuid
from Controller.hearing_controller import get_hearings
from Controller.doc_controller import get_documents
from Models.doc_model import Documentfilter


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
            "user_id": user_id,
            "ai_summary": None,
            "created_at": now,
            "updated_at": now,
        }

        await case_collection.insert_one(case_document)

        case_document["id"] = case_document.pop("_id")
        return {
            "success": True,
            "message": "Case created successfully",
            "data": CaseResponse(**case_document).dict(),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create case") from e


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

        return {
            "success": True,
            "message": "Cases fetched successfully",
            "data": cases,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch cases") from e


# get single case by id
async def get_case(case_id: str):
    try:
        case = await case_collection.find_one({"_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")
        case["id"] = str(case.pop("_id"))

        # Safely fetch hearings — a new case may have none, treat 404 as empty list
        try:
            hearings = await get_hearings(filter=None, case_id=case_id)
            case["hearings"] = hearings if isinstance(hearings, list) else []
        except HTTPException:
            case["hearings"] = []

        # Safely fetch documents — a new case may have none, treat 404 as empty list
        try:
            docs = await get_documents(Documentfilter(case_id=case_id))
            case["documents"] = docs if isinstance(docs, list) else []
        except HTTPException:
            case["documents"] = []

        return {
            "success": True,
            "message": "Case fetched successfully",
            "data": case,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch case") from e


# update case by id
async def update_case(case_id: str, update_data: CaseUpdate, user_id: str):
    try:
        existing = await case_collection.find_one({"_id": case_id})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Case not found."
            )

        if existing.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: You do not have permission to update this case."
            )

        fields_to_update = {
            key: value
            for key, value in update_data.dict().items()
            if value is not None
        }

        if not fields_to_update:
            raise HTTPException(status_code=400, detail="No fields provided to update.")

        fields_to_update["updated_at"] = datetime.now(timezone.utc)

        await case_collection.update_one(
            {"_id": case_id},
            {"$set": fields_to_update}
        )

        return {
            "success": True,
            "message": "Case updated successfully",
            "data": None,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update case") from e


# delete case by id
async def delete_case(case_id: str, user_id: str):
    try:
        existing = await case_collection.find_one({"_id": case_id})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Case not found."
            )

        if existing.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: You do not have permission to delete this case."
            )

        await case_collection.delete_one({"_id": case_id})
        return {
            "success": True,
            "message": "Case deleted successfully",
            "data": None,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete case") from e