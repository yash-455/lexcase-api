from bcrypt import hashpw, gensalt, checkpw

# hash a plain text password usong bcrypt
def hash_password(password: str) -> str:
    hased = hashpw(password.encode('utf-8'), gensalt())
    return hased.decode('utf-8')


# Verify a plain password against a hashed password
def verify_password(password: str, hashed_password: str) -> bool:
    return checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )