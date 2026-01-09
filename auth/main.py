from h11._readers import Http10Reader
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, utils
from auth_database import get_db
from jose import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError


SECRET_KEY = "t57t1AR5VSQyDeq5f2n6j8JeIrAKvQ-cBO4Xu_eJ2vo"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Helper function taht takes user data
def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt

app = FastAPI()

@app.post("/signup")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # check the user exit or not
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail= "Usernam already exist")

    # Hash the password
    hashed_pass = utils.hash_password(user.password)

    # Create new user instance
    new_user = models.User(
        username = user.username,
        email = user.email,
        hashed_password = hashed_pass,
        role=user.role
    )

    # Save user to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Reteurn the value (excluding password)
    return {'id': new_user.id, "username": new_user.username, "email": new_user.email, "role": new_user.role}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm =Depends(), db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Username")

    if not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Password")

    token_data = {'sub': user.username, 'role': user.role}
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credential",
    headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credential_exception

    except JWTError:
        raise credential_exception

    return {"username": username, "role": role}

@app.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    return {"Messege": f"Hello, {current_user['username']} | You accessed a protected route"}

def require_roles(allowed_roles: list[str]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permission")
            
        return current_user
    return role_checker

@app.get("/profile")
def profile(current_user: dict = Depends(require_roles(["user", "admin"]))):
    return {"messege": f"Profile of {current_user['username']} ({current_user['role']})"}

@app.get("/user/dashboard")
def user_dashboard(current_user: dict = Depends(require_roles(["user"]))):
    return {"messege": "Welcome User"}

@app.get("/admin/dashboard")
def user_dashboard(current_user: dict = Depends(require_roles(["admin"]))):
    return {"messege": "Welcome Admin"}