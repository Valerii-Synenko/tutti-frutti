import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, RevokedToken, User, get_db
from app.migrate import upgrade_to_head
from app.schemas import AccessToken, LogoutRequest, RefreshRequest, TokenPair, UserOut, UserRegister, UserUpdate
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


async def _seed_admin() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == "admin@admin.com"))
        if existing.scalar_one_or_none() is None:
            db.add(User(
                email="admin@admin.com",
                hashed_password=hash_password("admin"),
                full_name="Admin",
                is_admin=True,
            ))
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic's command API is synchronous; run it off the event loop thread
    # so startup doesn't block. The schema is brought to head automatically
    # on every boot — no manual `ALTER TABLE` or separate migrate step.
    await asyncio.to_thread(upgrade_to_head)
    await _seed_admin()
    yield


app = FastAPI(
    title="Tutti Frutti — Users Service",
    description="Handles registration, login and JWT issuance for the Tutti Frutti demo shop.",
    version="1.0.0",
    lifespan=lifespan,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        user_id = uuid.UUID(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise credentials_error

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "users-service"}


@app.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["user"], summary="Register")
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenPair, tags=["user"], summary="Login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # OAuth2PasswordRequestForm uses "username" as the field name; we treat it as the email.
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return TokenPair(
        access_token=create_access_token(str(user.id), is_admin=user.is_admin, is_seller=user.is_seller),
        refresh_token=create_refresh_token(str(user.id)),
    )


@app.post("/auth/refresh", response_model=AccessToken, tags=["user"], summary="Refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    revoked = await db.execute(select(RevokedToken).where(RevokedToken.jti == data.get("jti")))
    if revoked.scalar_one_or_none() is not None:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    try:
        user_id = uuid.UUID(data["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")

    return AccessToken(
        access_token=create_access_token(str(user.id), is_admin=user.is_admin, is_seller=user.is_seller)
    )


@app.get("/auth/me", response_model=UserOut, tags=["user"], summary="Get User")
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.patch("/auth/me", response_model=UserOut, tags=["user"], summary="Update User")
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.email is not None and payload.email != current_user.email:
        existing = await db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        current_user.email = payload.email

    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    if payload.password is not None:
        current_user.hashed_password = hash_password(payload.password)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@app.post("/auth/become-seller", response_model=TokenPair, tags=["user"], summary="Become Seller")
async def become_seller(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grants the seller role. Returns a fresh token pair since the seller
    claim is embedded in the access token for other services to check."""
    if not current_user.is_seller:
        current_user.is_seller = True
        await db.commit()
        await db.refresh(current_user)

    return TokenPair(
        access_token=create_access_token(
            str(current_user.id), is_admin=current_user.is_admin, is_seller=current_user.is_seller
        ),
        refresh_token=create_refresh_token(str(current_user.id)),
    )


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["user"], summary="Logout")
async def logout(
    payload: LogoutRequest = LogoutRequest(),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revokes the given refresh token so it can no longer be exchanged for a
    new access token. Requires a currently-valid access token, which is left
    to expire naturally (15 min) rather than tracked — only the long-lived
    refresh token needs explicit revocation."""
    if payload.refresh_token:
        try:
            data = decode_token(payload.refresh_token)
            jti = data.get("jti")
        except JWTError:
            jti = None
        if jti:
            existing = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
            if existing.scalar_one_or_none() is None:
                db.add(RevokedToken(jti=jti))
                await db.commit()
