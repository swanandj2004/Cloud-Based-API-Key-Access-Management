from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text 
from sqlalchemy.orm import Session 
from Database.database import session, engine 
from Schema import schema
from Entities import user, role, apikey
from pwdlib import PasswordHash
import secrets
from security.login import LoginRequest
import cryptography, os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

application = FastAPI()
password_hash = PasswordHash.recommended()
load_dotenv()
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]
cipher = Fernet(ENCRYPTION_KEY.encode())

from fastapi.middleware.cors import CORSMiddleware
from security import token


application.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

schema.Base.metadata.create_all(bind=engine)

def get_db():
    db = session()
    try:
        yield db 
    finally:
        db.close()

# user login
@application.post("/user/login")
def login(login: LoginRequest, db: Session = Depends(get_db)):
    check_username_query = text("""SELECT username FROM users WHERE username=:username""")
    existing_username = db.execute(check_username_query,{"username":login.form_username}).scalar()
    if existing_username == None or existing_username == "":
        raise HTTPException(status_code=401, detail="Invalid username")
    check_password_query = text("""SELECT password FROM users WHERE username=:username""")
    exisiting_password = db.execute(check_password_query, {"username":existing_username}).scalar()
    is_valid = password_hash.verify(login.form_password, exisiting_password)
    if is_valid:
        id_query = text("""SELECT id FROM users WHERE username=:username""")
        role_query = text("""SELECT role FROM users WHERE username=:username""")
        access_token = token.create_access_token(
            id = db.execute(id_query, {"username":existing_username}).scalar(),
            username = existing_username,
            role = db.execute(role_query, {"username":existing_username}).scalar()
        )
        return {"status": "success", "message": "User login successful", "access_token":access_token, "token_type":"bearer"}
    else:
        return {"status": "fail", "message": "Invalid username or password"}


# get all roles 
@application.get("/get/all/roles")
def getAllRoles(db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    roles = db.execute(text(f"SELECT * FROM roles")).mappings().all()
    return roles 
# get specific role 
@application.get("/get/role/{id}")
def getRole(id: int,db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    check_query = text("""SELECT * FROM roles WHERE id=:id""")
    existing_role = db.execute(check_query, {"id":id}).mappings().first()
    if existing_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    return existing_role
# create new role
@application.post("/create/role")
def createNewRole(role:role.Role,db: Session = Depends(get_db), user: dict | None = Depends(token.verify_token)):
    role_exists = db.execute(text("""SELECT 1 FROM roles WHERE name=:name"""),{"name":"admin"}).first()
    if role_exists is None:
        insert_query = text("""INSERT INTO roles(name) VALUES(:name)""")
        db.execute(insert_query,{"name":"admin"})
        db.commit()
        return {"status": "success", "message": "New role created successfully"}
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to this perform action")
    query = text("""INSERT INTO roles(name) VALUES(:name)""")
    role = db.execute(query,{"name":role.name})
    db.commit()
    return {"status":"success", "message":"New role created successfully"}
# update existing role
@application.put("/update/role/{id}")
def updateRole(id: int,new_role:role.Role,db:Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    check_query = text("""SELECT * FROM roles WHERE id=:id""") 
    exisitng_role = db.execute(check_query, {"id":id}).first()
    if exisitng_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    update_query = text("""UPDATE roles SET name=:name WHERE id=:id""")
    db.execute(update_query,{"name":new_role.name, "id":id})
    db.commit()
    return {"status":"success", "message":"Role updated successfully"}


# get all users 
@application.get("/get/all/users")
def getAllUsers(db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    required_role = db.execute(text("""SELECT id FROM roles WHERE name='admin'""")).scalar()
    if role_id!=required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to this action")
    users = db.execute(text(f"SELECT * FROM users")).mappings().all()
    return users 
# get specific user 
@application.get("/get/user/{id}")
def getUser(id: int, db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    user_id = user.get("id")
    required_role = db.execute(text("""SELECT id FROM roles WHERE name='admin'""")).scalar()
    if role_id==required_role or user_id==id:
        check_query = text("""SELECT * FROM users WHERE id=:id""")
        existing_user = db.execute(check_query, {"id":id}).mappings().first()
        if existing_user == None:
            raise HTTPException(status_code=404, detail="User doesn't exist")
        return existing_user
    raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
# create new user 
@application.post("/create/user")
def createUser(user:user.User,db: Session = Depends(get_db)):
    check_query = text("""SELECT * FROM users WHERE username=:username""")
    existing_user = db.execute(check_query, {"username":user.username}).first()
    if existing_user is not None:
        return "User already exists"
    role_query = text("""SELECT id FROM roles WHERE name=:role_name""")
    default_role = db.execute(role_query, {"role_name":"user"}).first()
    if default_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    insert_query = text("""INSERT INTO users(username,password,role) VALUES(:username,:password,(SELECT id FROM roles WHERE name='user'))""")
    hashed_password = password_hash.hash(user.password)
    user = db.execute(insert_query, {"username":user.username, "password":hashed_password})
    db.commit()
    return {"status": "success","message": "New user created successfully"} 
# create new admin
@application.post("/create/admin")
def createAdmin(user: user.User, db: Session = Depends(get_db), temp_user : dict | None = Depends(token.verify_token)):
    admin_exists = db.execute(text("""SELECT 1 FROM users WHERE role=(SELECT id FROM roles WHERE name='admin')""")).first()
    required_role = db.execute(text("""SELECT id FROM roles WHERE name='admin'""")).scalar()
    if admin_exists is None:
        hashed_password = password_hash.hash(user.password)
        insert_query = text("""INSERT INTO users(username, password, role) VALUES(:username, :password, :role)""")
        db.execute(insert_query, {"username":user.username, "password":hashed_password, "role":required_role})
        db.commit()
        return {"status": "success", "message": "Initial admin created"}
    role_id = temp_user.get("role")
    if role_id!=required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    check_query = text("""SELECT * FROM users WHERE username=:username""")
    existing_user = db.execute(check_query,{"username":user.username}).first()
    if existing_user is not None:
        return "User already exists"
    role_query = text("""SELECT id FROM roles WHERE name=:role_name""")
    default_role = db.execute(role_query,{"role_name":"admin"}).first()
    if default_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    insert_query = text("""INSERT INTO users(username, password, role) VALUES(:username,:password,(SELECT id FROM roles WHERE name='admin'))""")
    hashed_password = password_hash.hash(user.password)
    user = db.execute(insert_query,{"username":user.username, "password":hashed_password})
    db.commit()
    return {"status": "success", "message": "New admin created successfully"}
# update existing user
@application.put("/update/user/{id}")
def updateUser(id: int, user: user.User, db: Session = Depends(get_db), temp_user: dict = Depends(token.verify_token)):
    user_id = temp_user.get("id")
    if user_id!=id:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    check_query = text("""SELECT * FROM users WHERE id=:id AND role=(SELECT id FROM roles WHERE name='user')""")
    existing_user = db.execute(check_query, {"id":id}).first() 
    if existing_user == None:
        raise HTTPException(status_code=404, detail="User doesn't exist")
    hashed_password = password_hash.hash(user.password)
    update_query = text("""UPDATE users SET username=:username, password=:password WHERE id=:id""")
    db.execute(update_query, {"username":user.username, "password":hashed_password, "id":id})
    db.commit()
    return {"status":"success", "message": "User details updated successsfully"}
# update existing admin
@application.put("/update/admin/{id}")
def updateAdmin(id: int,admin: user.User, db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    user_id = user.get("id")
    if user_id!=id:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    check_query = text("""SELECT * FROM users WHERE id=:id AND role=(SELECT id FROM roles WHERE name='admin')""")
    existing_admin = db.execute(check_query,{"id":id}).first()
    if existing_admin == None:
        raise HTTPException(status_code=404, detail="User doesn't exist")
    hashed_password = password_hash.hash(admin.password)
    update_query = text("""UPDATE users SET username=:username, password=:password WHERE id=:id""")
    db.execute(update_query, {"username":admin.username, "password":hashed_password, "id":id})
    db.commit()
    return {"status": "success", "message": "Admin details updated successfully"}
# delete exiting user
@application.delete("/delete/user/{id}")
def deleteUser(id: int, db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    user_id = user.get("id")
    required_role = db.execute(text("""SELECT id FROM roles WHERE name='admin'""")).scalar()
    if role_id==required_role or user_id==id: 
        check_query = text("""SELECT * FROM users WHERE id=:id""")
        existing_user = db.execute(check_query,{"id":id}).first()
        if existing_user == None:
            raise HTTPException(status_code=404, detail="User doesn't exist")
        delete_query = text("""DELETE FROM users WHERE id=:id""")
        db.execute(delete_query,{"id":id})
        db.commit()
        return {"status": "success", "message": "User deleted successfully"}
    raise HTTPException(status_code=403, detail="You're not permitted to perform this action")


# generate api key
@application.post("/create/key")
def createApiKey(key: apikey.Key, db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    api_key = secrets.token_hex(32)
    encrypted_api_key = cipher.encrypt(api_key.encode()).decode()
    insert_query = text("""INSERT INTO keys(key, created_at, permitted_users) VALUES(:api_key, CURRENT_TIMESTAMP, :permitted_users)""")
    db.execute(insert_query, {"api_key":encrypted_api_key, "permitted_users":key.permitted_users})
    db.commit()
    return {"status": "success", "message": "API Key created successfully"}
# get all api keys
@application.get("/get/all/keys")
def getAllKeys(db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    get_query = text("""SELECT id, key, created_at, permitted_users FROM keys""")
    all_keys = db.execute(get_query).mappings().all()
    decrypted_keys = []
    for key in all_keys:
        plain_key = cipher.decrypt(key["key"].encode()).decode()
        decrypted_keys.append({
            "id":key["id"],
            "key":plain_key,
            "created_at":key["created_at"],
            "permitted_users":key["permitted_users"]
        })
    return decrypted_keys
# get specific key
@application.get("/get/key/{id}")
def getKey(id: int, db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You' re not permitted to perform this action")
    get_query = text("""SELECT id, key, created_at, permitted_users FROM keys WHERE id=:id""")
    result_key = db.execute(get_query, {"id":id}).mappings().first()
    result_key = dict(result_key)
    result_key["key"] = cipher.decrypt(result_key["key"].encode()).decode()
    return result_key
# delete api key
@application.delete("/delete/key/{id}")
def deleteKey(id: int, db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id!=token.required_role:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    delete_query = text("""DELETE FROM keys WHERE id=:id""")
    db.execute(delete_query, {"id":id})
    return {"status": "success", "message": "API Key deleted successfully"} 
# view api keys -> for user 
@application.get("/get/user/keys/{id}")
def getUserPermittedKeys(id: int, db: Session = Depends(get_db), user: dict = Depends(token.verify_token)):
    role_id = user.get("role")
    if role_id == token.required_role:
        return getAllKeys()
    user_id = user.get("id")
    if user_id!=id:
        raise HTTPException(status_code=403, detail="You're not permitted to perform this action")
    get_query = text("""SELECT key FROM keys WHERE :id=ANY(permitted_users)""")
    permitted_keys = db.execute(get_query, {"id":id}).scalars().all()
    decrypted_keys = []
    for key in permitted_keys:
        decrypted_keys.append(cipher.decrypt(key.encode()).decode())
    return decrypted_keys