from datetime import datetime, timedelta
def generate_temp_credential_package(account_name: str, password: str, otp_code: str, days: int = 3) -> dict:
    expires_at = datetime.utcnow() + timedelta(days=days)
    return {"login_id": account_name, "password": password, "otp_code": otp_code, "expires_at": expires_at.isoformat()}
