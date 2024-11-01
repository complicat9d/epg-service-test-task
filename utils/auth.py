from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated, Optional
from pydantic import BaseModel
from jwt.exceptions import PyJWTError

from database.session import SessionDep
from utils.hash import hasher
from utils.db.client import get_client, get_client_by_email
from utils.jwt import decode_token
from schemas.client import ClientSchema
from schemas.exception import (
    IncorrectPasswordException,
    ClientNotFoundException,
    ClientAuthenticationFailedException,
)
from schemas.security import TokenData


class AuthScheme(BaseModel):
    is_new: bool
    email: str
    password: str


oauth2_dep = Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="api/clients/login"))]
oauth2_form_dep = Annotated[OAuth2PasswordRequestForm, Depends()]


async def authenticate(
    email: str, password: str, session: SessionDep
) -> Optional[ClientSchema]:
    user = await get_client_by_email(email, session)
    if user is None:
        raise ClientNotFoundException
    if not hasher.verify_password(password, user.password):
        raise IncorrectPasswordException

    return user


async def get_current_client(token: oauth2_dep, session: SessionDep) -> ClientSchema:
    try:
        payload = decode_token(token)
        if payload:
            data = TokenData(**payload)
            return await get_client(data.sub, session)
        else:
            raise ClientAuthenticationFailedException

    except PyJWTError:
        raise ClientAuthenticationFailedException


client_dep = Annotated[ClientSchema, Depends(get_current_client)]