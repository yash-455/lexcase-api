from fastapi import HTTPException
from bson import ObjectId
from Models.user_model import User_update, User_delete, UserResponse
from DB.db_connect import user_collection
from Utils.password import hash_password, verify_password


# get current user
async def get_me(user_id: str):
    try:
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        return UserResponse(
            id=str(user["_id"]),
            name=user["name"],
            email=user["email"],
            firm_name=user.get("firm_name"),
            created_at=str(user["created_at"])
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# update user
async def update(user_id: str, user: User_update):
    try:
        update_data = user.dict(exclude_unset=True)

        if not update_data:
            return {"message": "No fields provided to update."}

        result = await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return {"message": "User not found."}

        if result.modified_count == 1:
            return {"message": "User updated successfully."}
        else:
            return {"message": "No changes made."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


# delete user (password required)
async def delete(user_id: str, user_data: User_delete):
    try:
        existing = await user_collection.find_one({"_id": ObjectId(user_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="User not found.")

        if not verify_password(user_data.password, existing["password"]):
            raise HTTPException(status_code=401, detail="Incorrect password. User not deleted.")

        await user_collection.delete_one({"_id": ObjectId(user_id)})
        return {"message": "User deleted successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}