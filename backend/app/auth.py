from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from app.database import get_database
from app.models import User, UserInDB, TokenData, PyObjectId

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
pwd_context = bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    database = await get_database()
    user_doc = await database.users.find_one({"email": email})
    if user_doc:
        user_id = user_doc.pop("_id", None)
        user = UserInDB(**user_doc)
        user.id = user_id
        return user
    return None


async def get_user_by_id(user_id: PyObjectId) -> Optional[UserInDB]:
    database = await get_database()
    user_doc = await database.users.find_one({"_id": user_id})
    if user_doc:
        return UserInDB(**user_doc)
    return None


async def create_user(user_data: dict) -> UserInDB:
    database = await get_database()
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()
    result = await database.users.insert_one(user_data)
    user_id = result.inserted_id
    user_data["_id"] = user_id
    # Remove _id from user_data before creating UserInDB, 
    # as Pydantic v2 has issues with PyObjectId validation
    user_data_no_id = {k: v for k, v in user_data.items() if k != "_id"}
    user_in_db = UserInDB(**user_data_no_id)
    user_in_db.id = user_id
    return user_in_db


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user