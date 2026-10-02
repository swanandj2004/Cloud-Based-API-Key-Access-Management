from pydantic import BaseModel 

class Key(BaseModel): 
    permitted_users: list[int]