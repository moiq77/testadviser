import sys
from passlib.context import CryptContext

# This uses the same hashing context as the server
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Hashes the provided password."""
    return pwd_context.hash(password)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash_password.py <your_password>")
        sys.exit(1)

    password_to_hash = sys.argv[1]
    hashed_password = get_password_hash(password_to_hash)

    print("Password hashing utility")
    print("------------------------")
    print(f"Password to hash: {password_to_hash}")
    print(f"Hashed password (for .env file): {hashed_password}")
    print("\nCopy the hashed password and set it as the ADMIN_PASSWORD_HASH in your .env file.")