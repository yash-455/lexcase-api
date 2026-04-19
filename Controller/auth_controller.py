from fastapi import HTTPException
from Models.auth_model import (
    User_register,
    User_login,
    Change_password,
    Forgot_password_request,
    Forgot_password_verify_otp,
    Forgot_password_reset,
)
from DB.db_connect import user_collection
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
            raise HTTPException(status_code=400, detail="Email already registered")

        user_dict["password"] = hash_password(user_dict["password"])

        user_dict["created_at"] = datetime.now(timezone.utc)

        result = await user_collection.insert_one(user_dict)
        return {
            "success": True,
            "message": "User registered successfully",
            "data": {"id": str(result.inserted_id)},
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to register user") from e


# login
async def login(user_login: User_login):
    try:
        user = await user_collection.find_one({"email": user_login.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(user_login.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({"email": user["email"], "id": str(user["_id"])})
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "token": token,
                "user": {
                    "id": str(user["_id"]),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "firm_name": user.get("firm_name"),
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed") from e


# change password
async def change_pass(user: Change_password):
    try:
        existing_user = await user_collection.find_one({"email": user.email})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(user.old_password, existing_user["password"]):
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        hashed_password = hash_password(user.new_password)
        result = await user_collection.update_one(
            {"email": user.email},
            {"$set": {"password": hashed_password}}
        )
        if result.modified_count == 1:
            return {
                "success": True,
                "message": "Password changed successfully",
                "data": None,
            }

        raise HTTPException(status_code=500, detail="Failed to change password")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to change password") from e


# forgot password: request otp
async def forgot_password_request_otp(user: Forgot_password_request):
    try:
        existing_user = await user_collection.find_one({"email": user.email})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Using a fixed OTP for testing while email delivery is not wired.
        fixed_otp = "123456"
        await user_collection.update_one(
            {"email": user.email},
            {
                "$set": {
                    "forgot_password_otp": fixed_otp,
                    "forgot_password_otp_verified": False,
                    "forgot_password_otp_created_at": datetime.now(timezone.utc),
                }
            },
        )
        return {
            "success": True,
            "message": "OTP generated successfully",
            "data": {"otp": fixed_otp},
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate OTP") from e


# forgot password: verify otp
async def forgot_password_verify_otp(user: Forgot_password_verify_otp):
    try:
        existing_user = await user_collection.find_one({"email": user.email})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        saved_otp = existing_user.get("forgot_password_otp")
        if not saved_otp:
            raise HTTPException(status_code=400, detail="Please request OTP first")

        if user.otp != saved_otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        await user_collection.update_one(
            {"email": user.email},
            {"$set": {"forgot_password_otp_verified": True}},
        )
        return {
            "success": True,
            "message": "OTP verified successfully",
            "data": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to verify OTP") from e


# forgot password: reset password after otp verification
async def forgot_password_reset(user: Forgot_password_reset):
    try:
        existing_user = await user_collection.find_one({"email": user.email})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not existing_user.get("forgot_password_otp_verified", False):
            raise HTTPException(status_code=400, detail="Please verify OTP before resetting password")

        hashed_password = hash_password(user.new_password)
        result = await user_collection.update_one(
            {"email": user.email},
            {
                "$set": {"password": hashed_password},
                "$unset": {
                    "forgot_password_otp": "",
                    "forgot_password_otp_verified": "",
                    "forgot_password_otp_created_at": "",
                },
            },
        )

        if result.modified_count == 1:
            return {
                "success": True,
                "message": "Password reset successfully",
                "data": None,
            }
        raise HTTPException(status_code=500, detail="Failed to reset password")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reset password") from e
