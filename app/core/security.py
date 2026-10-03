import hashlib
import hmac
import secrets


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)

    derived_key = hashlib.scrypt(
        pin.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=32,
    )

    return f"{salt.hex()}:{derived_key.hex()}"


def verify_pin(pin: str, stored_hash: str) -> bool:
    try:
        salt_hex, key_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)

        derived_key = hashlib.scrypt(
            pin.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            dklen=32,
        )

        return hmac.compare_digest(derived_key, expected_key)

    except (ValueError, TypeError):
        return False