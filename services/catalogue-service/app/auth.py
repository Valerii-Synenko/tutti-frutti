from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings

# tokenUrl points at users-service purely so Swagger/Zudoku "Authorize" flows resolve correctly;
# this service never issues tokens itself, it only verifies them.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


@dataclass
class AuthClaims:
    user_id: str
    is_admin: bool
    is_seller: bool


def _decode(token: str | None) -> AuthClaims:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return AuthClaims(
            user_id=payload["sub"],
            is_admin=bool(payload.get("is_admin", False)),
            is_seller=bool(payload.get("is_seller", False)),
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def require_auth(token: str | None = Depends(oauth2_scheme)) -> str:
    """Verifies a JWT issued by users-service. Returns the user id (sub claim)."""
    return _decode(token).user_id


async def require_claims(token: str | None = Depends(oauth2_scheme)) -> AuthClaims:
    """Like require_auth but also exposes the is_admin/is_seller claims."""
    return _decode(token)


async def require_seller(claims: AuthClaims = Depends(require_claims)) -> AuthClaims:
    if not claims.is_seller and not claims.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seller status required")
    return claims


async def require_admin(claims: AuthClaims = Depends(require_claims)) -> AuthClaims:
    if not claims.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin status required")
    return claims
