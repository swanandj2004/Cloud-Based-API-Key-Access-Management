from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text 
from sqlalchemy.orm import Session 
from Database.database import session, engine 
from Schema import schema
from Entities import user, role, apikey
from pwdlib import PasswordHash

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
    return role
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
    return new_role
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
    return "Role deleted sucessfully"


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
    hashed_password = password_hash.hash(user.password)
    role_query = text("""SELECT id FROM roles WHERE name=:role_name""")
    default_role = db.execute(role_query, {"role_name":"user"}).first()
    if default_role == None:
        raise HTTPException(status_code=404, detail="Role doesn't exist")
    insert_query = text("""INSERT INTO users(username,password,role) VALUES(:username,:password,(SELECT id FROM roles WHERE name='user'))""")
    user = db.execute(insert_query, {"username":user.username, "password":hashed_password})
    db.commit()
    return "New user created successfully" 
# update existing user
@application.put("/update/user/{id}")
def updateUser(id: int, user:user.User, db: Session = Depends(get_db)):
    check_query = text("""SELECT * FROM users WHERE id=:id""")
    existing_user = db.execute(check_query, {"id":id}).first() 
    if existing_user == None:
        raise HTTPException(status_code=404, detail="User doesn't exist")
    hashed_password = password_hash.hash(user.password)
    update_query = text("""UPDATE users SET username=:username, password=:password WHERE id=:id""")
    user = db.execute(update_query, {"username":user.username, "password":hashed_password, "id":id})
    db.commit()
    return user 
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
    return "User deleted successfully"