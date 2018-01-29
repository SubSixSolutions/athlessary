from passlib.handlers.pbkdf2 import pbkdf2_sha256


def hash_password(password):
    hashed_pass = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)
    return hashed_pass