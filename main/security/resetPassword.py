from pydantic import BaseModel

class resetPasswordRequest(BaseModel):
    password: str