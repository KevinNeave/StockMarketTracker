from requests import get
from datetime import datetime as dt
from pprint import PrettyPrinter
import re

printer = PrettyPrinter()

API_KEY = "C2O7P9R31LW4XLIG"
BASE_URL = "https://www.alphavantage.co/query"
pattern = re.compile("[0-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]")

def getDailySeries (stock):
    endpoint = f"?function=TIME_SERIES_DAILY&symbol={stock}&apikey={API_KEY}&outputsize=compact"
    url = BASE_URL + endpoint
    data=get(url).json()
    if "Note" in data:
        print("Rate limit reached. Try again in a minute.")
        return None
    return data.get("Time Series (Daily)")

def closeValue (stock, day):
    data = getDailySeries(stock)
    if not re.fullmatch(pattern, day):
        print("Date not in valid format!")
        return
    dayData = data.get(day)
    while not dayData:
        today = day[-2:]
        todayInt = int(today)
        prevDayInt = todayInt -1
        prevDay = str(prevDay)
        if(prevDayInt == 0):
            print("Not available today")
            return
        day.replace(today, prevDay)
        dayData = data.get(day)
    closeVal = dayData["4. close"]
    print(f"{stock} value = {closeVal}")
    return closeVal
    
def portfolioValue (stocks) :
    total = 0
    for stock, amount in stocks:
        val = float(closeValue(stock)) * float(amount)
        total += val

    print(f"Total Portfolio Value = ${total}")
    return val

def percentChange (stock, day1, day2):
    day1Val = closeValue(stock, day1)
    day2Val = closeValue(stock, day2)
    change = float(day1Val) - float(day2Val)
    fraction = change / float(day2Val)
    percent = fraction * 100
    print(f"{stock} is {percent} over this time period")

    return percent

val = percentChange("NFLX", "2025-04-07", "2025-04-17")