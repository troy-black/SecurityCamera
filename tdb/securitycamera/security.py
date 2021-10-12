from datetime import datetime
from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from tdb.securitycamera import config
from tdb.securitycamera.models import UserDetails
from tdb.securitycamera.utilities import OAuth2PasswordBearerWithCookie

oath2 = OAuth2PasswordBearerWithCookie(auth_url='auth')
crypt = CryptContext(schemes=['bcrypt'], deprecated='auto')


def password_verify(plain: str, hashed: str):
    return crypt.verify(plain, hashed)


def password_hash(plain: str):
    return crypt.hash(plain)


def authenticate_user(username: str, password: str):
    user = config.Config.users.get(username)

    if not user:
        return False

    if not password_verify(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, config.Config.secret_key, algorithm='HS256')

    return encoded_jwt


async def get_current_user(token: str = Depends(oath2)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = jwt.decode(token, config.Config.secret_key, algorithms=['HS256'])
        username: str = payload.get('sub')

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = config.Config.users.get(username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: UserDetails = Depends(get_current_user)):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail='Inactive user')

    return current_user
