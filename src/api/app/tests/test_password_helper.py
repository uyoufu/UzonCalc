from utils.password_helper import hash_password, verify_password


def test_hash_password_can_be_verified():
    hashed_password, salt = hash_password("demo-password")

    assert hashed_password
    assert salt
    assert verify_password("demo-password", hashed_password, salt)
    assert not verify_password("wrong-password", hashed_password, salt)
