from pydantic import BaseModel
from role import Role

class User(BaseModel):
    id: int 
    username: str 
    password: str 
    role: Role