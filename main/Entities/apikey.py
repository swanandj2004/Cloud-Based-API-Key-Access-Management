from pydantic import BaseModel 

class Key(BaseModel):
    id: int 
    key: str 