import requests

# Base URL of the Gold API that returns the current global gold price
GOLD_API_URL = "https://api.gold-api.com/price/XAU"


def get_gold_price() -> dict[str, object]:
    """
    قیمت لحظه‌ای جهانی طلا را برای هر انس به دلار برمی‌گرداند.

    Returns:
        dict: شامل symbol, price_usd_per_ounce, name.

    Raises:
        RuntimeError: اگر گرفتن یا خواندن قیمت طلا ناموفق باشد.
    """
    # Fetch the latest gold price from the Gold API.
    # A timeout is set so the request does not hang indefinitely.
    try:
        response = requests.get(GOLD_API_URL, timeout=10)

        # Raise an HTTPError for bad responses (4xx / 5xx).
        response.raise_for_status()

        # Parse the response body as JSON.
        data = response.json()

    # Any network / HTTP-level problem is wrapped in a RuntimeError.
    except requests.RequestException as exc:
        raise RuntimeError("دریافت قیمت جهانی طلا ناموفق بود.") from exc

    # Invalid JSON payload from the API is also wrapped in a RuntimeError.
    except ValueError as exc:
        raise RuntimeError("پاسخ Gold API معتبر نیست.") from exc

    # Make sure the expected "price" field actually exists
    # before trying to use it.
    if "price" not in data:
        raise RuntimeError("قیمت طلا در پاسخ Gold API وجود ندارد.")

    # Return a normalized, well-typed result.
    return {
        "symbol": data.get("symbol", "XAU"),
        "price_usd_per_ounce": float(data["price"]),
        "name": data.get("name", "Gold"),
    }