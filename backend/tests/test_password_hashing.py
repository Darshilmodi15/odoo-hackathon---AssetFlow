from app.core.security import hash_password, verify_password


def test_argon2_hash_generation_and_verification():
    password = "test-password-" + ("x" * 100)
    hashed = hash_password(password)

    assert hashed.startswith("$argon2")
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_malformed_hash_returns_false():
    assert verify_password("password", "not-a-valid-hash") is False
