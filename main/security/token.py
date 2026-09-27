from jose import jwt, JWTError
from datetime import timezone, timedelta, datetime
import os 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException

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
        "id":id,
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

security = HTTPBearer()

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):  
    access_token = credentials.credentials
    try:
        payload = jwt.decode (
            access_token,
            SECRET_KEY,
            algorithm=[ALGORITHM]
        )
        id = payload.get("id")
        username = payload.get("username")
        role = payload.get("role")

        if id == None or username == None or role == None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id":id, "username":username, "role":role}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

required_role = 9