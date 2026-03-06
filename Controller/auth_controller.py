from fastapi import HTTPException
from bson import ObjectId
from Models.auth_model import User_register, User_login
from DB.mongo import user_collection
from Utils.jwt_handler import create_access_token
from Utils.password import hash_password, verify_password
from datetime import datetime, timezone


# register
async def register(user_register: User_register):
    try:
        user_dict = user_register.dict()

        # check if email already registered
        existing_user = await user_collection.find_one({"email": user_register.email})
        if existing_user:
            return {"message": "Email already registered"}

        user_dict["password"] = hash_password(user_dict["password"])
        user_dict["created_at"] = datetime.now(timezone.utc)   # ✅ added from PDF schema

        result = await user_collection.insert_one(user_dict)
        return {"message": "User registered successfully", "id": str(result.inserted_id)}

    except Exception as e:
        return {"error": str(e)}


# login
async def login(user_login: User_login):
    try:
        user = await user_collection.find_one({"email": user_login.email})
        if not user:
            return {"message": "User not found"}
        if not verify_password(user_login.password, user["password"]):
            return {"message": "Invalid password"}

        token = create_access_token({"email": user["email"], "id": str(user["_id"])})  # ✅ added id to token
        return {"token": token}

    except Exception as e:
        return {"error": str(e)}


# change password
async def change_pass(user: User_login):
    try:
        existing_user = await user_collection.find_one({"email": user.email})
        if not existing_user:
            return {"message": "User not found"}

        hashed_password = hash_password(user.password)
        result = await user_collection.update_one(
            {"email": user.email},
            {"$set": {"password": hashed_password}}
        )
        if result.modified_count == 1:
            return {"message": "Password changed successfully"}
        else:
            return {"message": "Failed to change password"}

    except Exception as e:
        return {"error": str(e)}