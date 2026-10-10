from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, is_db_connected
from app.core import security
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from app.db.base import Base

# Setup in-memory sqlite engine for DEMO_MODE
demo_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
DemoSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=demo_engine)
for table in Base.metadata.sorted_tables:
    try:
        table.create(demo_engine)
    except Exception as e:
        pass

def get_db() -> Generator:
    demo_mode = os.environ.get("DEMO_MODE", "true").lower() == "true"
    if demo_mode:
        db = DemoSessionLocal()
    else:
        if not is_db_connected():
            raise HTTPException(status_code=503, detail="Database connection failed")
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_optional() -> Generator:
    demo_mode = os.environ.get("DEMO_MODE", "true").lower() == "true"
    if demo_mode:
        db = DemoSessionLocal()
    else:
        if not is_db_connected():
            yield None
            return
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        # Fallback for prototype when DB is down
        fallback_users = {
            "admin": User(id=1, username="admin", email="admin@climatetwin.local", role="admin", is_active=True),
            "operator": User(id=2, username="operator", email="operator@climatetwin.local", role="operator", is_active=True),
            "viewer": User(id=3, username="viewer", email="viewer@climatetwin.local", role="viewer", is_active=True)
        }
        if username in fallback_users:
            return fallback_users[username]
        raise credentials_exception

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role: {user.role}"
            )
        return user



