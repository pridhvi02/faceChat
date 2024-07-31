from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import numpy as np
import logging
import io
from models.user import User
from pkg.recognition.voice_recognition import extract_voice_features
from pkg.recognition.face_recognition import recognize_face
from pkg.gemini.gemini_services import get_gemini_response
from database import get_db


router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

image_embedding=np.array([[]])
voice_embedding=np.array([[]])

def find_closest_vector (db : Session, image_vector: np.ndarray, voice_vector: np.ndarray, threshold:float=0.90):
    logger.info("Checking Similarity between vector embeddings in Database")
    matched_user_id = None
    image_list=image_vector.tolist()[0]
    voice_list=voice_vector.tolist()[0]
        
    query = f"""
    SELECT user_id,name,(face_image <=> :image_vector) AS image_similarity,(voice_sample <=> :voice_vector) AS voice_similarity
    FROM users
    WHERE (face_image <=> :image_vector) >= :threshold AND (voice_sample <=> :voice_vector) >= :threshold
    ORDER BY (face_image <=> :image_vector + voice_sample <=> :voice_vector) DESC
    LIMIT 1;
    """
    result=db.execute(query,{'image_vector':image_list,'voice_vector':voice_list,'threshold':threshold}).fetchone()  #dictionary is returned
    
    if result :
        matched_user_id=result['user_id']
        matched_user_name=result['name']
        logger.info(f"Matched user ID: {matched_user_id}, Name: {matched_user_name} with similarity: {result['similarity']}")
        return matched_user_id,matched_user_name
    else:
        logger.error(f"No Matching User, the Highest similarity is {result['similarity']}")
        return 'No Match Found'
        


@router.post("app/auth/verify")
async def verify_user(file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    file_name=file.filename
    file_ext=file_name.split('.')[-1].lower()
    
    #function to retrieve image embedding
    async def image():
        try:
            image_bytes=file.read()
            global image_embedding
            image_embedding= recognize_face(io.BytesIO(image_bytes))
            logger.info(f"Extracted Image vector successfully: {image_embedding}")
                            
        except Exception as e:
            logger.error(f"Error in extracting the image embedding or similarity search in DB {e}")
            raise
    
    #function to retrieve voice embedding
    async def voice():
        logger.info("Received voice file for verification")
        try:
            file_bytes = await file.read()
            global voice_embedding
            voice_embedding = extract_voice_features(io.BytesIO(file_bytes))
            logger.info(f"Extracted voice vector: {voice_embedding}")
            
        except Exception as e:
            logger.error(f"Error extracting voice vector: {e}")
            raise HTTPException(status_code=500, detail="Error extracting voice vector")

        
    #condition to divide the image and voice file
    if file_ext in ['jpg','png','jpeg']:
        image()
    elif file_ext in ['wav','mp3','aiff']:
        voice()
    else :
        raise HTTPException(status_code=404, detail="Unsupported File Type")
    
    
    #Handling the result got from the similarity search
    search_result= find_closest_vector(db,image_embedding,voice_embedding)
    if isinstance(search_result,tuple):                        #checking if the returned item is a tuple with userid and user name
        logger.info("Matching user found")
        user_id,user_name=search_result
    else:
        logger.info("No matching user found")
        raise HTTPException(status_code=404, detail="User not found")

    response = get_gemini_response(user_id,user_name)
    logger.info(f"Generated response from Gemini: {response}")
    return {"user_id": user_id, "response": response}
    
    
#------------------------------------------------------------------------------------------------------------------------------------------------#


def insert_user(db: Session, user_id: str, name: str, age: int, gender: str, contact: str, face_image: np.ndarray, voice_sample: np.ndarray):
    try:
        # Create a new User object
        new_user = User(
            user_id= user_id,
            name=name,
            age=age,
            gender=gender,
            contact=contact,
            face_image=face_image.tolist()[0],
            voice_sample=voice_sample.tolist()[0]
        )
    
        db.add(new_user)       # Commit the session to the database
        db.commit()
        db.refresh(new_user)  # Refresh the session to get the new user's ID
        logger.info('Sucessfully inserted the User Details in the Database')
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting user: {e}")
        return None



def update_user(db: Session, user_id: int, name: str = None, age: int = None, gender: str = None, 
                contact: str = None, face_image: np.ndarray = None, voice_sample: np.ndarray = None):
    try:
        # Query the user by ID
        user = db.query(User).filter(User.user_id == user_id).one_or_none()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return None
        
        # Update the user's details if provided
        if name:
            user.name = name
        if age:
            user.age = age
        if gender:
            user.gender = gender
        if contact:
            user.contact = contact
        if face_image is not None:
            user.face_image = face_image.tolist()[0]  # Convert numpy array to list
        if voice_sample is not None:
            user.voice_sample = voice_sample.tolist()[0]  # Convert numpy array to list
        
        # Commit the session to the database
        db.commit()
        # Refresh the session to get the updated user's details
        db.refresh(user)
        logger.info('Sucessfully Updated the User Details in the Database')
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        return None

    

@router.post("app/auth/register")
async def register_user(file: UploadFile = File(...), db: Session = Depends(get_db)):
    insert_user()
    update_user()
    
    
    
    
    
    
    
    
