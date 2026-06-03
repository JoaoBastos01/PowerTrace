"""Authentication dependencies for protected API routes.

This is intentionally only a skeleton. Keep the API shape stable first,
then choose the actual auth strategy.
"""

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import AuthenticatedUser
from app.security import decode_access_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthenticatedUser:
    """Return the authenticated user for protected routes."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    token = credentials.credentials
    
    try:
        #TODO: Validar token JWT  
        payload = decode_access_token(token)
        
        # TODO: pegar subject do token
        subject = payload.get("sub")

        # TODO: se não tiver subject, token é inválido
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject.",
            )

    except jwt.ExpiredSignatureError:
        # TODO: token expirado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired token.",
        )

    except jwt.InvalidTokenError:
        # TODO: token inválido
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

    # TODO: por enquanto, o usuário autenticado é o próprio subject
    return AuthenticatedUser(
        id=subject,
        username=subject,
    )

