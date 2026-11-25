import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

def verify_telegram_init_data(init_data: str, bot_token: str, max_age: int = 86400):
    """Verify Telegram Mini App initData. Returns user dict or None."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = pairs.pop("hash", None)
        if not received_hash:
            return None

        auth_date = int(pairs.get("auth_date", "0"))
        if auth_date <= 0 or abs(time.time() - auth_date) > max_age:
            return None

        data_check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(pairs.items())
        )
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        user = json.loads(pairs.get("user", "{}"))
        return user if isinstance(user, dict) and "id" in user else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
