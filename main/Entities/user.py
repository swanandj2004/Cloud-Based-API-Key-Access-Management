from pydantic import BaseModel
from Entities.role import Role

class User(BaseModel): 
    username: str 
    password: str 