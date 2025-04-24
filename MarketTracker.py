from functools import lru_cache 
from requests import get
from datetime import datetime as dt, timedelta
from pprint import PrettyPrinter
from dotenv import load_dotenv
import re
import os

load_dotenv()

printer = PrettyPrinter()

AAPI_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "MISSING_KEY")

#Check if missing key
if AAPI_KEY == "MISSING_KEY":
    raise RuntimeError("Set your keys in .env (see .env.example)")

ABASE_URL = "https://www.alphavantage.co/query"
CBASE_URL = "https://api.frankfurter.dev/v1/"
pattern = re.compile("[0-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]")

BASE_CUR = "USD"


#Get todays date
def getDate() -> str | None:
    return dt.now().strftime("%Y-%m-%d")
#Alphavantage Api call
@lru_cache(maxsize=None)
def getDailySeries (stock: str) -> dict[str, dict] | None:
    endpoint = f"?function=TIME_SERIES_DAILY&symbol={stock}&apikey={AAPI_KEY}&outputsize=compact"
    url = ABASE_URL + endpoint
    data=get(url).json()
    if "Note" in data:
        print("Rate limit reached. Try again in a minute.")
        return None
    if "Error Message" in data:
        print("API error: ", data["Error Message"])
    return data.get("Time Series (Daily)")

#Get currency stock is valued in
@lru_cache(maxsize=None)
def getCurrency (stock: str) -> str | None:
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": stock,
        "apikey": AAPI_KEY
    }

    r = get(ABASE_URL, params=params)
    data = r.json().get("bestMatches", [])
    if not data: 
        print(f"No currency matches found for {stock}")
        return None
    match = data[0]
    return match.get("8. currency")


#Calculate the exchange rate of given currencies
@lru_cache(maxsize=None)
def exchangeRate(currency1: str, currency2: str) -> float | None:
    endpoint = f"latest?symbols={currency2}&base={currency1}"
    url = CBASE_URL + endpoint
    data = get(url).json()['rates']
    if len(data) == 0:
        print("Invalid currencies.")
        return None
    
    rate = list(data.values())[0]
    print(f"{currency1} -> {currency2} = {rate}")
    
    return rate

#Find the close value of a given stock on a given day
def closeValue (stock: str, day: str) -> float | None:
    data = getDailySeries(stock)
    if data is None:
        return None
    if not re.fullmatch(pattern, day):
        print("Date not in valid format!")
        return None
    current = day
    while current not in data:
        dateObj = dt.strptime(current, "%Y-%m-%d") - timedelta(dayes=1)
        current = dateObj.strftime("%Y-%m-%d")
        if dateObj.year < 2000:
            print("No trading data available on {day}")
            return None
    dayData = data[current]
    price = float(dayData["4. close"])
    curr = getCurrency(stock) or BASE_CUR
    exchange = exchangeRate(curr, BASE_CUR) or 1
    converted = price * exchange
    print(f"{stock} value = {converted}")
    return converted

#Calculate the value of a given portfolio
def portfolioValue (stocks: list[tuple[str, float]]) -> float | None :
    total = 0.0
    for stock, amount in stocks:
        val = float(closeValue(stock, getDate())) * float(amount)
        total += val

    print(f"Total Portfolio Value = ${total}")
    return val

#Calculate the percent change of a stock over a time period given by 2 days
def percentChange (stock: str, day1: str, day2: str) -> float | None:
    data = getDailySeries(stock)
    if data is None:
        return None
    curr = getCurrency(stock)
    exchange = exchangeRate(curr, BASE_CUR)
    
    def getClose(day: str) -> float:
        if not re.fullmatch(pattern,day):
            raise ValueError("Invalid date format")
        current = day
        while current not in data:
            dateObj = dt.strptime(current, "%Y-%m-%d") - timedelta(days=1)
            current = dateObj.strftime("%Y-%m-%d")
            if dateObj.year < 2000:
                raise ValueError(f"No trading data available before {day}")
        dayData = data[current]
        return float(dayData["4. close"]) * exchange
    
    try:
        day1Price = getClose(day1)
        day2Price = getClose(day2)
    except ValueError as e:
        print(e)
        return None
    
    pct = (day1Price - day2Price) / day2Price * 100
    print(f"{stock} changed by {pct}% from {day1} to {day2}")
    return pct

#Change the base currency of the program
def changeCurrency(currency) -> None:
    endpoint = f"latest"
    url = CBASE_URL + endpoint
    data = get(url).json()['rates']
    if currency in data:
        print(f"{currency} is a valid currency, the base currency has been changed to {currency}")
        BASE_CUR = currency

    else:
        print(f"{currency} is not a valid currency, the base currency is still {BASE_CUR}")

    return None


val = percentChange("NFLX", "2025-04-07", "2025-04-17")