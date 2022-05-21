import email
from email.policy import HTTP
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from ..schemas import User, db, UserResponse
import secrets
from ..utils import get_password_hash
from ..send_email import send_registration_mail


router = APIRouter(
    tags=["User Routes"]
)


@router.post("/registration", response_description="Register a user", response_model=UserResponse)
async def registration(user_info: User):
    user_info = jsonable_encoder(user_info)

    # check for duplication
    username_found = await db["users"].find_one({"name": user_info["name"]})
    email_found = await db["users"].find_one({"email": user_info["email"]})

    if username_found:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Username is already taken")
    
    if email_found:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email id already taken")

    # hash user password
    user_info["password"] = get_password_hash(user_info["password"])
    # create apikey
    user_info["apiKey"] = secrets.token_hex(30)

    new_user = await db["users"].insert_one(user_info)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})

    await send_registration_mail("Registration Successful", user_info["email"], {
        "title": "Regitration Succeful",
        "name": user_info["name"]
    })

    return created_user
    


