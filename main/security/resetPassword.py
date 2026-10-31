from pydantic import BaseModel

class resetPasswordRequest(BaseModel):
    username: str
    password: str