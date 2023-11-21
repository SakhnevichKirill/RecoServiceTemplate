from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing_extensions import Annotated

from ..log import app_logger
from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    User,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_active_user,
)
from .exceptions import ModelNotFoundError, UserNotFoundError


class RecoResponse(BaseModel):
    user_id: int
    items: List[int]


router = APIRouter(prefix="/recsys")


@router.post(
    path="/login",
    response_model=Token,
    tags=["Auth"],
)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Login route for only 1 user in database

    Args:
        
        username (str): user name "johndoe".
        password (str): user password "secret".
    
    Returns:
        
        access_token: access token
        token_type: bearer
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    path="/users/me/",
    response_model=User,
    tags=["Auth"],
)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@router.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse("/recsys/docs")


@router.get(
    path="/health",
    tags=["Health"],
)
async def health(current_user: Annotated[User, Depends(get_current_active_user)]):
    '''
    It basically sends a GET request to the route & hopes to get a "200"
    response code. Failing to return a 200 response code just enables
    the GitHub Actions to rollback to the last version the project was
    found in a "working condition". It acts as a last line of defense in
    case something goes south.
    Additionally, it also returns a JSON response in the form of:
    
    {
        'healtcheck': 'Everything OK!'
    }
    '''
    return {'healthcheck': 'Everything OK!'}


@router.get(
    path="/reco/{model_name}/{user_id}",
    tags=["Recommendations"],
    response_model=RecoResponse,
)
async def get_reco(
    request: Request, model_name: str, user_id: int, current_user: Annotated[User, Depends(get_current_active_user)]
) -> RecoResponse:
    """
    Recommendations from a model for user_id

    Args:

        model_name (str): only the "popular" model is available.
        user_id (int): id of the user waiting for the recommendation.
    
    Returns:
    
        RecoResponse: recs for user
    """
    app_logger.info(f"Request for model: {model_name}, user_id: {user_id}")

    if user_id > 10**9:
        raise UserNotFoundError(error_message=f"User {user_id} not found")
    k_recs = request.app.state.k_recs

    if model_name == "popular":  # popular interactions model for last 7 days
        top10_recs = request.app.state.recsys_models["pop_model"].recommend(N=k_recs)
        return RecoResponse(user_id=user_id, items=top10_recs)
    raise ModelNotFoundError(error_message=f"Model {model_name} not found")


def add_views(app: FastAPI) -> None:
    app.include_router(router)
