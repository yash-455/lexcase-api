from Models.auth_model import User_register, User_login, RegisterVerification
from DB.db_connect import user_collection, registration_code_collection
from Utils.jwt_handler import create_access_token
from Utils.password import hash_password, verify_password
from datetime import datetime, timezone
from datetime import timedelta
from secrets import randbelow
from Utils.email_sender import send_registration_code_email


REGISTRATION_CODE_TTL_MINUTES = 10


def _generate_6_digit_code() -> str:
    return f"{randbelow(1_000_000):06d}"


# register
async def register(user_register: User_register):
    try:
        # check if email already registered
        existing_user = await user_collection.find_one({"email": user_register.email})
        if existing_user:
            return {"message": "Email already registered"}

        user_dict = user_register.dict()
        user_dict["password"] = hash_password(user_dict["password"])

        code = _generate_6_digit_code()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=REGISTRATION_CODE_TTL_MINUTES)

        await registration_code_collection.update_one(
            {"email": user_register.email},
            {
                "$set": {
                    "email": user_register.email,
                    "code": code,
                    "expires_at": expires_at,
                    "user_data": user_dict,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

        email_sent = send_registration_code_email(user_register.email, code)
        if not email_sent:
            return {
                "message": "Failed to send verification code email. Check SMTP configuration."
            }

        return {
            "message": "Verification code sent to email. Please verify to complete registration."
        }

    except Exception as e:
        return {"error": str(e)}


# verify registration code and complete account creation
async def verify_register_code(payload: RegisterVerification):
    try:
        # if user already created, block duplicate registration
        existing_user = await user_collection.find_one({"email": payload.email})
        if existing_user:
            return {"message": "Email already registered"}

        pending = await registration_code_collection.find_one({"email": payload.email})
        if not pending:
            return {"message": "No pending registration found for this email"}

        now = datetime.now(timezone.utc)
        if pending.get("expires_at") and pending["expires_at"] < now:
            return {"message": "Verification code expired"}

        if pending.get("code") != payload.code:
            return {"message": "Invalid verification code"}

        user_dict = pending.get("user_data")
        if not user_dict:
            return {"message": "Invalid pending registration data"}

        user_dict["created_at"] = now
        result = await user_collection.insert_one(user_dict)

        await registration_code_collection.delete_one({"email": payload.email})

        return {
            "message": "User registered successfully",
            "id": str(result.inserted_id),
        }
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

        token = create_access_token({"email": user["email"], "id": str(user["_id"])})  # added id to token
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