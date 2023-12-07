from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from databases import Database
from generateToken import create_access_token, expiration_time, decode_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = "./db/db.db"
database = Database(DATABASE_URL)

users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "secret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "secret2",
        "disabled": True,
    },
}

app = FastAPI()


def hash_all_password():
    # hash database passwords
    for user in users_db:
        users_db[user]["hashed_password"] = pwd_context.hash(
            users_db[user]["hashed_password"]
        )
        print(users_db[user]["hashed_password"])


hash_all_password()


def hash_password(password):
    return pwd_context.hash(password)


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


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    decodedUser = decode_access_token(token)["sub"]
    user = get_user(users_db, decodedUser)
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username")
    user = UserInDB(**user_dict)

    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    access_token_expires = expiration_time()
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.post("/user")
async def create_user(user: UserCreate):
    # check if user exists
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    # create user with hashed password
    user_data = user.create_user()
    # add user to database
    users_db[user.username] = user_data
    # return user data
    return user_data


@app.patch("/updateuser")
async def update_user(
    updated_user: UserCreate,
    current_user: User = Depends(get_current_active_user),
):
    current_user.username = updated_user.username
    current_user.email = updated_user.email
    current_user.full_name = updated_user.full_name

    if not pwd_context.verify(updated_user.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return current_user


@app.get("/users")
async def read_users():
    # Remove hashed passwords before returning the user data
    users_data = [
        {k: v for k, v in user.items() if k != "hashed_password"} for user in users_db.values()
    ]
    return users_data
