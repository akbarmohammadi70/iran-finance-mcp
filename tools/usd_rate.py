import os

import requests
from dotenv import load_dotenv

# Load environment variables from the .env file (e.g. NAVASAN_API_KEY).
load_dotenv()


def get_usd_rate() -> dict[str, object]:
    """
    آخرین نرخ دلار آمریکا به تومان را از Navasan دریافت می‌کند.

    Returns:
        dict: شامل usd_sell_toman و last_update.

    Raises:
        RuntimeError: اگر API Key تنظیم نشده باشد یا دریافت اطلاعات
            ناموفق باشد.
    """

    # Read the API key from the environment.
    api_key = os.getenv("NAVASAN_API_KEY")

    # Fail fast if the API key has not been configured.
    if not api_key:
        raise RuntimeError("NAVASAN_API_KEY در فایل .env تنظیم نشده است.")

    # Base URL of the Navasan "latest" endpoint.
    url = "https://api.navasan.tech/latest/"

    # Fetch the latest rates from Navasan.
    # A timeout is set so the request does not hang indefinitely.
    try:
        response = requests.get(url, params={"api_key": api_key}, timeout=10)

        # Raise an HTTPError for bad responses (4xx / 5xx).
        response.raise_for_status()

        # Parse the response body as JSON.
        data = response.json()

    # Any network / HTTP-level problem is wrapped in a RuntimeError.
    except requests.RequestException as exc:
        raise RuntimeError("دریافت نرخ دلار از Navasan ناموفق بود.") from exc

    # Invalid JSON payload from the API is also wrapped in a RuntimeError.
    except ValueError as exc:
        raise RuntimeError("پاسخ Navasan معتبر نیست.") from exc

    # Extract the USD entry from the response and normalize its fields.
    # Missing or malformed fields are treated as an unexpected schema.
    try:
        usd_info = data["usd"]
        return {
            "usd_sell_toman": float(usd_info["value"]),
            "last_update": usd_info["date"],
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "ساختار پاسخ Navasan با ساختار مورد انتظار مطابقت ندارد."
        ) from exc