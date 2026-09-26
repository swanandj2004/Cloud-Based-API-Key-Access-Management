from jose import jwt
from datetime import timezone, timedelta, datetime
import os 

SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30 
ALGORITHM = "HS256"

def create_access_token(
        id: int,
        username: str,
        role: int
):

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "id":str(id),
        "username":username,
        "role":role,
        "exp":expire
    }

    encoded_jwt = jwt.encode (
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )  
    return encoded_jwt