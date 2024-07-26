from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    age: int
    contact: str
    face_image: list[float]
    voice_sample: list[float]
    conversation: list[float]