from pydantic import BaseModel

class forgotPasswordRequest(BaseModel):
    username: str