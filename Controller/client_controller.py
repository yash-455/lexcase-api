from fastapi import HTTPException
from bson import ObjectId
from Models.client_model import ClientCreate, ClientUpdate, ClientResponse
from DB.mongo import client_collection, case_collection
from datetime import datetime, timezone


# add new client
async def add_client(client: ClientCreate, user_id: str):
    try:
        # check if client with same email already exists for this lawyer
        if client.email:
            existing = await client_collection.find_one(
                {
                    "email": client.email,
                    "user_id": user_id
                }
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Client with email '{client.email}' already exists."
                )

        now = datetime.now(timezone.utc)

        client_document = {
            **client.dict(),
            "user_id": user_id,             # which lawyer this client belongs to
            "created_at": now,
        }

        result = await client_collection.insert_one(client_document)

        client_document["id"] = str(result.inserted_id)
        client_document.pop("_id", None)

        return ClientResponse(**client_document)

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get all clients — search by name
async def get_clients(search: str = None, user_id: str = None):
    try:
        query = {}

        # only return clients belonging to logged in lawyer
        if user_id:
            query["user_id"] = user_id

        # partial case-insensitive search by name
        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        cursor = client_collection.find(query)

        clients = []
        async for client in cursor:
            client["id"] = str(client.pop("_id"))
            clients.append(client)

        if not clients:
            raise HTTPException(
                status_code=404,
                detail="No clients found."
            )

        return clients

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get single client by id
async def get_client(client_id: str):
    try:
        client = await client_collection.find_one({"_id": ObjectId(client_id)})
        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found."
            )

        client["id"] = str(client.pop("_id"))
        return client

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# get all cases belonging to a client
async def get_client_cases(client_id: str):
    try:
        # check if client exists first
        client = await client_collection.find_one({"_id": ObjectId(client_id)})
        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found."
            )

        cursor = case_collection.find({"client_id": client_id})

        cases = []
        async for case in cursor:
            case["id"] = str(case.pop("_id"))
            cases.append(case)

        if not cases:
            raise HTTPException(
                status_code=404,
                detail="No cases found for this client."
            )

        return cases

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# update client
async def update_client(client_id: str, update_data: ClientUpdate):
    try:
        existing = await client_collection.find_one({"_id": ObjectId(client_id)})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Client not found."
            )

        fields_to_update = {
            key: value
            for key, value in update_data.dict().items()
            if value is not None
        }

        if not fields_to_update:
            return {"message": "No fields provided to update."}

        await client_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": fields_to_update}
        )

        return {"message": "Client updated successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# delete client
async def delete_client(client_id: str):
    try:
        existing = await client_collection.find_one({"_id": ObjectId(client_id)})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Client not found."
            )

        await client_collection.delete_one({"_id": ObjectId(client_id)})
        return {"message": "Client deleted successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}