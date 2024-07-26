from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import numpy as np
import logging
import io
from models.user import User
from pkg.recognition.voice_recognition import extract_voice_features
from pkg.gemini.gemini_services import get_gemini_response
from database import get_db
from scipy.spatial.distance import euclidean

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_closest_voice_match(db: Session, voice_vector: np.ndarray, threshold: float = 50.0):
    logger.info(f"Finding closest match for voice vector: {voice_vector}")
    users = db.query(User).all()
    matched_user_id = None
    for user in users:
        logger.info(f"Comparing with user: {user.user_id}, voice sample: {user.voice_sample}")
        distance = euclidean(user.voice_sample, voice_vector)
        if distance < threshold:
            matched_user_id = user.user_id
            break
    logger.info(f"Matched user ID: {matched_user_id}")
    return matched_user_id

@router.post("/auth/verify")
async def verify_user(file: UploadFile = File(...), db: Session = Depends(get_db)):
    logger.info("Received voice file for verification")
    try:
        file_bytes = await file.read()
        voice_vector = extract_voice_features(io.BytesIO(file_bytes))
        logger.info(f"Extracted voice vector: {voice_vector}")
    except Exception as e:
        logger.error(f"Error extracting voice vector: {e}")
        raise HTTPException(status_code=500, detail="Error extracting voice vector")

    user_id = find_closest_voice_match(db, voice_vector)
    if user_id is None:
        logger.info("No matching user found")
        raise HTTPException(status_code=404, detail="User not found")

    response = get_gemini_response(user_id)
    logger.info(f"Generated response from Gemini: {response}")
    return {"user_id": user_id, "response": response}

@router.post("/auth/register")
async def register_user(name: str, age: int, gender: str, contact: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    logger.info("Received registration data")
    try:
        file_bytes = await file.read()
        voice_vector = extract_voice_features(io.BytesIO(file_bytes))
        logger.info(f"Extracted voice vector for registration: {voice_vector}")
    except Exception as e:
        logger.error(f"Error extracting voice vector: {e}")
        raise HTTPException(status_code=500, detail="Error extracting voice vector")

    new_user = User(name=name, age=age, gender=gender, contact=contact, voice_sample=voice_vector)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user registered with ID: {new_user.user_id}")
    return {"user_id": new_user.user_id, "message": "User registered successfully"}
