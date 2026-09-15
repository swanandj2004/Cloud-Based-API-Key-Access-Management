from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text 
from sqlalchemy.orm import Session 
from Database.database import session, engine 
from Schema import schema
from Entities import user, role, apikey
from pwdlib import PasswordHash

application = FastAPI()

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
def getRole(role: role.Role, id: int,db: Session = Depends(get_db)):
    role = db.execute(text(f"SELECT * FROM roles WHERE id={id}")).mappings().first()
    if role!=None:
        return role 
    return HTTPException(status_code=404, detail="Role doesn't exist")
# create new role
@application.post("/create/role")
def createNewRole(role:role.Role,db: Session = Depends(get_db)):
    db.execute(text("INSERT INTO roles VALUES('{role.name}')"))
    db.commit()
    return role
# update existing role
@application.put("/update/role/{id}")
def updateRole(id: int,role:role.Role,db:Session = Depends(get_db)):
    role = db.execute(text(f"SELECT * FROM roles WHERE id={id}")).first()
    if role == None:
        return HTTPException(status_code=404, detail="Role doesn't exist")
    db.execute(text(f"UPDATE roles SET name={role.name} WHERE id={id}"))
    db.commit()
    return role 
# delete existing role 
@application.delete("/delete/role/{id}")
def deleteRole(id:int,db: Session = Depends(get_db)):
    role = db.execute(text(f"SELECT * FROM roles WHERE id={id}")).first()
    if role == None:
        return HTTPException(status_code=404, detail="Roles doesn't exist")
    db.execute(text(f"DELETE FROM roles WHERE id={id}"))
    db.commit()
    return "Role Deleted"


# get all users 
@application.get("/get/all/users")
def getAllUsers(db: Session = Depends(get_db)):
    users = db.execute(text(f"SELECT * FROM users")).mappings().all()
    return users 
# get specific user 
@application.get("/get/user/{id}")
def getUser(id: int, db: Session = Depends(get_db)):
    user = db.execute(text(f"SELECT * FROM users WHERE id={id}")).mappings().first() 
    return user 