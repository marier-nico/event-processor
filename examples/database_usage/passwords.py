# This is NOT how you do it in a real application, this is just for the demo.
# For real password hashing, look at https://passlib.readthedocs.io/en/stable/.
def hash_password(password: str) -> str:
    return f"hashed-{password}"


# This is ALSO NOT how you do it in a real application, this is just for the demo.
# For real password hashing, look at https://passlib.readthedocs.io/en/stable/.
def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password
