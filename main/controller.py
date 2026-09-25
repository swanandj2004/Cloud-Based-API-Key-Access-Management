from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text 
from sqlalchemy.orm import Session 
from Database.database import session, engine 
from Schema import schema
from Entities import user, role, apikey
from Entities.user import User
from Entities.role import Role
from Entities.apikey import Key
from pwdlib import PasswordHash
import secrets
import bcrypt
from datetime import time, timezone, timedelta
from security.login import LoginRequest

application = FastAPI()
password_hash = PasswordHash.recommended()

schema.Base.metadata.create_all(bind=engine)

def get_db():
    db = session()
    try:
        yield db 
    finally:
        db.close()
# get all roles 
@application.get("/get/all/roles")
def getAllRoles(db: Session = Depends(get_db)):
    roles = db.execute(text(f"SELECT * FROM roles")).mappings().all()
    return roles 
# get specific role 
@application.get("/get/role/{id}")
def getRole(id: int,db: Session = Depends(get_db)):
    check_query = text("""SELECT * FROM roles WHERE id=:id""")
    existing_role = db.execute(check_query, {"id":id}).mappings().first()
    if existing_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    return existing_role
# create new role
@application.post("/create/role")
def createNewRole(role:role.Role,db: Session = Depends(get_db)):
    query = text("""INSERT INTO roles(name) VALUES(:name)""")
    role = db.execute(query,{"name":role.name})
    db.commit()
    return {"status":"success", "message":"New role created successfully"}
# update existing role
@application.put("/update/role/{id}")
def updateRole(id: int,new_role:role.Role,db:Session = Depends(get_db)):
    check_query = text("""SELECT * FROM roles WHERE id=:id""") 
    exisitng_role = db.execute(check_query, {"id":id}).first()
    if exisitng_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    update_query = text("""UPDATE roles SET name=:name WHERE id=:id""")
    db.execute(update_query,{"name":new_role.name, "id":id})
    db.commit()
    return {"status":"success", "message":"Role updated successfully"}
# delete existing role 
@application.delete("/delete/role/{id}")
def deleteRole(id:int,db: Session = Depends(get_db)):
    check_query = text("""SELECT * FROM roles WHERE id=:id""")
    existing_role = db.execute(check_query, {"id":id}).first()
    if existing_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    delete_query = text("""DELETE FROM roles WHERE id=:id""")
    db.execute(delete_query, {"id":id})
    db.commit()
    return {"status":"success","message":"Role deleted successfully"}


# get all users 
@application.get("/get/all/users")
def getAllUsers(db: Session = Depends(get_db)):
    users = db.execute(text(f"SELECT * FROM users")).mappings().all()
    return users 
# get specific user 
@application.get("/get/user/{id}")
def getUser(id: int, db: Session = Depends(get_db)):
    check_query = text("""SELECT * FROM users WHERE id=:id""")
    existing_user = db.execute(check_query, {"id":id}).mappings().first()
    if existing_user == None:
        raise HTTPException(status_code=404, detail="User doesn't exist")
    return existing_user
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
def createAdmin(user: user.User, db: Session = Depends(get_db)):
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
def updateUser(id: int, user:user.User, db: Session = Depends(get_db)):
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
def updateAdmin(id: int,admin: user.User, db: Session = Depends(get_db)):
    check_query = text("""SELECT * FROM users WHERE id=:id AND role=(SELECT id FROM roles WHERE name='admin')""")
    existing_admin = db.execute(check_query,{"id":id}).first()
    if existing_admin == None:
        raise HTTPException(status_code=404, detail="User doesn't exist")
    hashed_password = password_hash.hash(admin.password)
    update_query = text("""UPDATE users SET username=:username, password:password WHERE id=:id""")
    db.execute(update_query, {"username":admin.username, "password":hashed_password, "id":id})
    db.commit()
    return {"status": "success", "message": "Admin details updated successfully"}
# delete exiting user
@application.delete("/delete/user/{id}")
def deleteUser(id: int, db: Session = Depends(get_db)):
    check_query = text("""SELECT * FROM users WHERE id=:id""")
    existing_user = db.execute(check_query,{"id":id}).first()
    if existing_user == None:
        raise HTTPException(status_code=404, detail="User doesn't exist")
    delete_query = text("""DELETE FROM users WHERE id=:id""")
    db.execute(delete_query,{"id":id})
    db.commit()
    return {"status": "success", "message": "User deleted successfully"}


# generate api key
@application.post("/create/key")
def createApiKey(key: apikey.Key, db: Session = Depends(get_db)):
    key = secrets.token_hex(32)
    hashed_key = password_hash.hash(key)
    insert_query = text("""INSERT INTO keys(key, created_at) VALUES(:api_key, CURRENT_TIMESTAMP)""")
    db.execute(insert_query, {"api_key":hashed_key})
    db.commit()
    return {"status": "success", "message": "API Key created successfully"}
# get all api keys
@application.get("/get/all/keys")
def getAllKeys(db: Session = Depends(get_db)):
    get_query = text("""SELECT * FROM keys""")
    keys = db.execute(get_query).mappings().all()
    return keys
# get specific key
@application.get("/get/key/{id}")
def getKey(id: int, db: Session = Depends(get_db)):
    get_query = text("""SELECT * FROM keys WHERE id=:id""")
    key = db.execute(get_query, {"id":id}).mapping().first()
    return key 
# delete api key
@application.delete("/delete/key/{id}")
def deleteKey(id: int, db: Session = Depends(get_db)):
    delete_query = text("""DELETE FROM keys WHERE id=:id""")
    db.execute(delete_query, {"id":id})
    return {"status": "success", "message": "API Key deleted successfully"}


# User Login
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
        return {"status": "success", "message": "User login successful"}
    else:
        return {"status": "fail", "message": "Invalid username or password"}