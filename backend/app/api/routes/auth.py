"""
Authentication API routes for AegisScan.
Handles user registration, login, profile inspection, and session verification.
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from loguru import logger

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_current_user
)
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user operator account in AegisScan.
    """
    logger.info(f"USER_REGISTRATION_ATTEMPT: email='{user_in.email}' username='{user_in.username}'")

    # Check if email exists
    if db.query(User).filter(User.email == user_in.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Check if username exists
    if db.query(User).filter(User.username == user_in.username.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists."
        )

    # If this is the very first user in the system, automatically grant admin status
    user_count = db.query(User).count()
    is_admin = True if user_count == 0 else (user_in.is_admin or False)

    new_user = User(
        email=user_in.email.lower(),
        username=user_in.username.lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_admin=is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"USER_REGISTERED_SUCCESS: id={new_user.id} username='{new_user.username}' is_admin={new_user.is_admin}")
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: Optional[UserLogin] = None,
    form_data: Optional[OAuth2PasswordRequestForm] = Depends(lambda: None),
    db: Session = Depends(get_db)
):
    """
    Authenticate user credentials and issue a signed JWT access token.
    Supports both JSON payload and standard OAuth2 form submission.
    """
    identifier = ""
    password = ""

    if login_data:
        identifier = login_data.username_or_email.strip().lower()
        password = login_data.password
    elif form_data:
        identifier = form_data.username.strip().lower()
        password = form_data.password
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login credentials must be provided via JSON body or form data."
        )

    user = db.query(User).filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"LOGIN_FAILED: identifier='{identifier}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"LOGIN_INACTIVE_USER: id={user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Please contact an administrator."
        )

    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=expires_delta,
        is_admin=user.is_admin
    )

    logger.info(f"LOGIN_SUCCESS: user_id={user.id} username='{user.username}'")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get profile information of the currently authenticated user.
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Stateless logout endpoint. Instructs client to discard stored tokens.
    """
    if current_user:
        logger.info(f"USER_LOGGED_OUT: id={current_user.id}")
    return {"message": "Successfully logged out. Please clear your authentication token."}


@router.get("/status")
async def get_auth_status(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Return system authentication status and whether initial setup is required.
    """
    user_count = db.query(User).count()
    return {
        "auth_enabled": True,
        "users_registered": user_count,
        "setup_required": user_count == 0,
        "authenticated": current_user is not None,
        "current_user": UserResponse.model_validate(current_user) if current_user else None
    }
