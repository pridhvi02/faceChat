from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    age: int
    contact: str
    face_image: str
    voice_sample: str