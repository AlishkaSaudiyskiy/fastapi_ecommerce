from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from passlib.context import CryptContext

from typing import Annotated

from datetime import datetime, timedelta

from jose import jwt, JWTError

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.schemas import CreateUser
from app.backend.db_depends import get_db


SECRET_KEY = 'b8e33e3630788f56ceb16f5aea2f2929db2dd5c6fb9a95103a3296105243ab20'
ALGORITHM = 'HS256'

router = APIRouter(prefix="/auth", tags=['auth'])
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def create_access_token(username: str, user_id: int, is_admin: bool, is_supplier: bool, is_customer: bool, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'is_admin': is_admin, 'is_supplier': is_supplier, 'is_customer': is_customer}
    expires = datetime.now() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def authanticate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.hashed_password) or user.is_active == "False":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        user_id = payload.get('id')
        is_admin = payload.get('is_admin')
        is_supplier = payload.get('is_supplier')
        is_customer = payload.get('is_customer')
        expire = payload.get('exp')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if datetime.now() > datetime.fromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )

        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_supplier': is_supplier,
            'is_customer': is_customer,
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )


@router.post('/token')
async def login(db: Annotated[AsyncSession, Depends(get_db)], form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authanticate_user(db, form_data.username, form_data.password)

    if not user or user.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    
    token = await create_access_token(
        user.username, 
        user.id, 
        user.is_admin, 
        user.is_supplier, 
        user.is_customer, 
        expires_delta=timedelta(minutes=20)
        )

    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.get('/read_current_user')
async def read_current_user(user: User = Depends(get_current_user)):
    return user


@router.post("/")
async def create_user(db: Annotated[AsyncSession, Depends(get_db)], create_user: CreateUser):
    await db.execute(insert(User).values(
        first_name=create_user.first_name,
        last_name=create_user.last_name,
        username=create_user.username,
        email=create_user.email,
        hashed_password=bcrypt_context.hash(create_user.password),
    ))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }