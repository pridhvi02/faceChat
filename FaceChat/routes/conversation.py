from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from models.user import User
from pkg.gemini import gemini_services

router = APIRouter()

@router.post("/message")
async def send_message(user_id: int, message: str):
    # Send message to user
    user = await User.get(user_id)
    if user:
        # Use Gemini API to generate response
        response = await gemini_services.generate_response(message, user.id)
        return JSONResponse(content={"response": response}, status_code=200)
    return JSONResponse(content={"message": "User not found"}, status_code=404)