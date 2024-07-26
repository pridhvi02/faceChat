from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from models.user import User
from pkg.recognition import face_recognition, voice_recognition

router = APIRouter()

@router.post("/verify")
async def verify_user(face_image: str, voice_sample: str):
    # Verify user using face and voice recognition
    user = await face_recognition.verify_user(face_image)
    if user:
        # Verify voice sample
        voice_verified = await voice_recognition.verify_user(voice_sample, user.id)
        if voice_verified:
            return JSONResponse(content={"message": "Welcome back"}, status_code=200)
    return JSONResponse(content={"message": "User not found. Please register."}, status_code=401)

@router.post("/register")
async def register_user(user: User):
    # Register new user
    # ...
    pass

@router.post("/conflict")
async def conflict_user(user: User):
    # user conflict
    # ...
    pass