from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from generateToken import create_access_token, expiration_time, decode_access_token

from databases import Database
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, Boolean, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, Session

from sqlalchemy.orm import Session

import os
from bardapi import BardCookies
from dotenv import load_dotenv
load_dotenv()

cookie_dict = {
    "__Secure-1PSID": os.getenv("BARD_TOKEN"),
    "__Secure-1PSIDTS": os.getenv("BARD_TOKEN_TS"),
    # Any cookie values you want to pass session object.
}

bard = BardCookies(cookie_dict=cookie_dict)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DATABASE_URL = "sqlite:///../db/db.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String(50), unique=True, index=True),
    Column("email", String(50), index=True, nullable=True),
    Column("full_name", String(50), index=True, nullable=True),
    Column("hashed_password", String(100), nullable=False),
    Column("disabled", Boolean, nullable=True),
)

user_history = Table(
    "user_history",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String(50), ForeignKey("users.username"), index=True),
    Column("prompt", Text, nullable=False),
    Column("historia", Text, nullable=False),
    Column("titulo", String(50), nullable=False),
    Column("categoria", String(50), nullable=False),
)

metadata.create_all(bind=engine)
    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class UserCreate(User):
    username: str
    email: str | None = None
    full_name: str | None = None
    password: str | None = None
    hashed_password: str = None
    disabled: bool | None = None

    def create_user(self):
        # hash password
        self.hashed_password = pwd_context.hash(self.password)
        # disable user
        self.disabled = False
        return self.model_dump()

    def model_dump(self):
        return {
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "hashed_password": self.hashed_password,
            "disabled": self.disabled,
        }

class Historia(BaseModel):
    titulo: str
    historia: str | None = None
    categoria: str

class HistoriaInDB(Historia):
    prompt: str



def hash_password(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    query = users.select().where(users.c.username == username)
    result = db.execute(query)
    user = result.fetchone()
    if user:
        return UserInDB(**user)
    return None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = get_user(db, username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    db.close()

    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = expiration_time()
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/user")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if get_user(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = user.create_user()
    # add user to database
    query = users.insert().values(new_user)
    result = db.execute(query)
    db.commit()
    return new_user



@app.patch("/updateuser")
async def update_user(
    user: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Garanta que o campo hashed_password seja fornecido
    if user.password:
        user.hashed_password = pwd_context.hash(user.password)
    
    # Remova o campo password para evitar problemas
    user.password = None

    # Convert UserCreate to a dictionary
    user_dict = user.model_dump()

    # update user in database
    query = users.update().where(users.c.username == current_user.username).values(user_dict)
    result = db.execute(query)
    db.commit()
    return user_dict




@app.delete("/deleteuser")
async def delete_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = users.delete().where(users.c.username == current_user.username)
    result = db.execute(query)
    db.commit()
    return {"message": "User deleted successfully"}
    

@app.get("/users")
async def read_users(db: Session = Depends(get_db)):
    query = users.select().with_only_columns([users.c.id, users.c.username, users.c.email, users.c.full_name, users.c.disabled])
    result = db.execute(query)
    users_without_passwords = [dict(user) for user in result.fetchall()]
    return users_without_passwords

@app.get("/usersdebug")
async def read_users_password(db: Session = Depends(get_db)):
    query = users.select()
    result = db.execute(query)
    return result.fetchall()

@app.post("/story")
async def create_historia(
    historia: Historia,
    authentication: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not authentication:
        raise HTTPException(status_code=401, detail="User not authenticated")
    # check if titulo already exists
    if db.execute(user_history.select().where(user_history.c.titulo == historia.titulo)).fetchone():
        raise HTTPException(status_code=400, detail="Titulo already exists")
    prompt = "Complete a historia da categoria " + historia.categoria + "..." + historia.historia
    response = bard.get_answer(prompt)['content']
    query = user_history.insert().values(username=authentication.username, prompt=prompt, historia=response, titulo=historia.titulo, categoria=historia.categoria)
    result = db.execute(query)
    db.commit()
    return response

@app.get("/stories")
async def read_historia(
    authentication: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not authentication:
        raise HTTPException(status_code=401, detail="User not authenticated")
    query = user_history.select()
    result = db.execute(query)
    return result.fetchall()

@app.patch("/updatestory")
async def update_historia(
    historia: Historia,
    authentication: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not authentication:
        raise HTTPException(status_code=401, detail="User not authenticated")
    query = user_history.update().where(user_history.c.titulo == historia.titulo).where(user_history.c.categoria == historia.categoria).values(historia=historia.historia)
    result = db.execute(query)
    db.commit()
    return historia.historia

@app.delete("/deletestory")
async def delete_historia(
    historia: Historia,
    authentication: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not authentication:
        raise HTTPException(status_code=401, detail="User not authenticated")
    titulo = historia.titulo
    categoria = historia.categoria
    query = user_history.delete().where(user_history.c.titulo == titulo).where(user_history.c.categoria == categoria)
    result = db.execute(query)
    db.commit()
    return {"message": "Historia deleted successfully"}



# python -m uvicorn app:app --reload