from jose import JWTError, jwt

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"

# create the jwt token
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# veryfies the access token 
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print("JWT token error:", e)
        return None

        
# token = create_access_token({"password": 123})
# print("TOKEN",token)

# decode = verify_access_token(token)
# print("DECODED DATA", decode)
