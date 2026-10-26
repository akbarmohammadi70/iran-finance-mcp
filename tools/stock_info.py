from datetime import datetime, timezone
from typing import Any

import pytse_client as tse


def get_stock_info(symbol: str) -> dict[str, Any]:
    """
    اطلاعات لحظه‌ای یک نماد بورسی ایران را از TSETMC بازمی‌گرداند.

    Args:
        symbol (str): نماد سهم، مثلاً "فولاد".

    Returns:
        dict: شامل symbol, name, last_price, price_change_percent,
            volume, market_cap, last_update.

    Raises:
        ValueError: اگر نماد پیدا نشود.
    """

    # Validate that the symbol is a non-empty string.
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("نماد سهم نمی‌تواند خالی باشد.")

    # Normalize the symbol (remove leading/trailing whitespace).
    symbol = symbol.strip()

    # Try to create a Ticker object for the given symbol.
    # Any failure here means the symbol is unknown to TSETMC.
    try:
        stock = tse.Ticker(symbol)
    except Exception as exc:
        raise ValueError(f"نماد '{symbol}' در TSETMC پیدا نشد.") from exc

    # Extract the basic fields we need.
    # If they are missing or unparsable, treat the symbol as not found.
    try:
        name = stock.title
        last_price = float(stock.last_price)
    except Exception as exc:
        raise ValueError(f"نماد '{symbol}' در TSETMC پیدا نشد.") from exc

    # Reject the result if the required fields are empty/zero.
    if not name or not last_price:
        raise ValueError(f"نماد '{symbol}' در TSETMC پیدا نشد.")

    # Read yesterday's price if available (used to compute % change).
    yesterday_price = getattr(stock, "yesterday_price", None)

    # Default price change to 0.0 when there is no previous price.
    price_change_percent = 0.0
    if yesterday_price:
        price_change_percent = (
            (last_price - float(yesterday_price)) / float(yesterday_price)
        ) * 100

    # Read trading volume, defaulting to 0 when missing.
    volume = int(getattr(stock, "volume", 0) or 0)

    # Market cap is not currently provided by pytse_client,
    # so we keep it as None for now.
    market_cap = None

    # Return a normalized, well-typed result.
    return {
        "symbol": symbol,
        "name": str(name),
        "last_price": last_price,
        "price_change_percent": round(price_change_percent, 2),
        "volume": volume,
        "market_cap": market_cap,
        "last_update": datetime.now(timezone.utc).isoformat(),
    }