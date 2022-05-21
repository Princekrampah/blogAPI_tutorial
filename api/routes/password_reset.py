from ast import Pass
from click import get_current_context
from fastapi import APIRouter, HTTPException, status
from httpcore import request


from ..schemas import PasswordReset, db, NewPassword
from ..oath2 import create_access_token, get_current_user
from ..send_email import password_reset
from ..utils import get_password_hash

router = APIRouter(
    prefix="/password",
    tags=["Password reset"]
)


@router.post("", response_description="Reset password")
async def reset_request(user_email: PasswordReset):
    user = await db["users"].find_one({"email": user_email.email})

    if user is not None:
        token = create_access_token({"id": user["_id"]})

        reset_link = f"http://localhost:8000/?token={token}"

        # TODO: send email

        await password_reset("Password Reset", user["email"], {
            "title": "Password Reset",
            "name": user["name"],
            "reset_link": reset_link
        })

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your with this email not found"
        )

    
@router.put("", response_description="Reset password")
async def reset(token: str, new_password: NewPassword):
    request_data = {k: v for k, v in new_password.dict().items() if v is not None}

    request_data["password"] = get_password_hash(request_data["password"])

    if len(request_data) >= 1:
        user = await get_current_user(token)

        update_result = await db["users"].update_one({"_id": user["_id"]}, {"$set": request_data})

        if update_result.modified_count == 1:
            updated_user = await db["users"].find_one({"_id": user["_id"]})

            if(updated_user) is not None:
                return updated_user
                
    existing_user = await db["users"].find_one({"_id": user["_id"]})

    if(existing_user) is not None:
        return  existing_user

    raise HTTPException(
        status_code=404, detail="User information not found on the server"
    )
