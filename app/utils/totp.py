import pyotp
def generate_totp_secret() -> str:
    return pyotp.random_base32()
def get_totp_uri(secret: str, account_name: str, issuer: str = "ChessPlatform") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)
def verify_totp(secret: str, otp: str) -> bool:
    return pyotp.TOTP(secret).verify(otp)
