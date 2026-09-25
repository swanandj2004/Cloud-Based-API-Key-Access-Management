from pydantic import BaseModel

class LoginRequest(BaseModel):
    form_username: str 
    form_password: str 