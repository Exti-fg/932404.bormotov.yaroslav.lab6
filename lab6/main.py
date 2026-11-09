import math
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

RATES = {
    ("USD", "EUR"): Decimal("0.92"),
    ("EUR", "RUB"): Decimal("105"),
    ("USD", "RUB"): Decimal("92"),
}
CURRENCIES = {"USD", "EUR", "RUB"}

app = FastAPI(title="Конвертер валют", description="Лабораторная работа №6")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/about", include_in_schema=False)
def about() -> FileResponse:
    return FileResponse(STATIC_DIR / "about.html")


@app.get("/service-worker.js", include_in_schema=False)
def service_worker() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "service-worker.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


@app.get("/api/status")
def status() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "currency-converter",
        "rates": {"USD_EUR": 0.92, "EUR_RUB": 105, "USD_RUB": 92},
    }


def get_rate(from_currency: str, to_currency: str) -> Decimal:
    if from_currency == to_currency:
        return Decimal("1")

    direct_rate = RATES.get((from_currency, to_currency))
    if direct_rate is not None:
        return direct_rate

    reverse_rate = RATES.get((to_currency, from_currency))
    if reverse_rate is not None:
        return Decimal("1") / reverse_rate

    raise HTTPException(status_code=400, detail="Неизвестная валютная пара.")


@app.get("/api/convert")
def convert(
    from_currency: str = Query(alias="from"),
    to_currency: str = Query(alias="to"),
    amount: str = Query(),
) -> dict[str, str | float]:
    from_currency = from_currency.strip().upper()
    to_currency = to_currency.strip().upper()

    if from_currency not in CURRENCIES or to_currency not in CURRENCIES:
        raise HTTPException(status_code=400, detail="Неизвестная валюта.")

    try:
        amount_value = Decimal(amount)
    except InvalidOperation as error:
        raise HTTPException(
            status_code=400, detail="Сумма должна быть положительным числом."
        ) from error

    if not amount_value.is_finite() or amount_value <= 0:
        raise HTTPException(
            status_code=400, detail="Сумма должна быть положительным числом."
        )

    rate = get_rate(from_currency, to_currency)
    result = amount_value * rate

    try:
        amount_number = float(amount_value)
        result_number = round(float(result), 2)
    except (OverflowError, ValueError) as error:
        raise HTTPException(
            status_code=400, detail="Сумма слишком велика для обработки."
        ) from error

    if not math.isfinite(amount_number) or not math.isfinite(result_number):
        raise HTTPException(
            status_code=400, detail="Сумма слишком велика для обработки."
        )

    return {
        "from": from_currency,
        "to": to_currency,
        "amount": amount_number,
        "result": result_number,
        "rate": float(rate),
    }
