import json
import requests
import os
import sys
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

UNIT_SECONDS = "second"
UNIT_MINUTES = "minute"
UNIT_HOURS = "hour"
UNIT_DAYS = "day"

CACHING_ENABLED=True
DATA_DIR="/home/timb/tb/stocks/.cache/"
API_KEY_FILE="api.key"

MOVING_AVERAGES_DAYS=[10, 50, 200]
MOVING_AVERAGES_MINUTES=[5,10,30]
MOVING_AVERAGE_LOOKBACK_DAYS=300

class PriceEntry:
    def __init__(self, avgPrice, openPrice, closePrice, transactions, high, low, volume, startTime, stopTime):
        self.AvgPrice = avgPrice
        self.OpenPrice = openPrice
        self.ClosePrice = closePrice
        self.Transactions = transactions
        self.High = high
        self.Low = low
        self.Volume = volume
        self.StartTime = startTime
        self.StopTime = stopTime

class Config:
    def __init__(self, ticker, startDate, stopDate, units, multiplier, apiKey):
        self.Ticker = ticker
        self.StartDate = startDate
        self.StopDate = stopDate
        self.Units = units
        self.Multiplier = multiplier
        self.ApiKey = apiKey


def ReadUserInput():
    ticker = input("Enter ticker: ")
    startDate = input("Enter startDate (unix time): ")
    stopDate = input("Enter stopDate (unix time): ")

    # try to load apikey from config
    apiKey = ""
    filePath = os.path.join(DATA_DIR, API_KEY_FILE)
    if os.path.exists(filePath):
        print("Cached API key found in: {}".format(filePath))
        with open(filePath, "r") as fd:
            apiKey = fd.readline().strip()
    else:
        apiKey = input("Enter polygon api key: ")
        with open(filePath, "w") as fd:
            fd.write(apiKey)

    return Config(ticker, startDate, stopDate, "minute", 1, apiKey)

def FetchData(config):
    filename = "{}-{}-{}-{}-{}.json".format(config.Ticker, config.Multiplier, config.Units, config.StartDate, config.StopDate)
    if CACHING_ENABLED:
        filePath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filePath):
            print("Data found in cache...using cache")
            with open(filePath, "r") as fd:
                return json.load(fd)
    url = "https://api.polygon.io/v2/aggs/ticker/{}/range/{}/{}/{}/{}?apiKey={}".format(config.Ticker, config.Multiplier, config.Units, config.StartDate, config.StopDate, config.ApiKey)
    response = requests.get(url)

    if response.status_code > 300:
        print("Failed to fetch data for ticker: "+config.Ticker)
        sys.exit(1)

    if CACHING_ENABLED:
        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)
        filePath = os.path.join(DATA_DIR, filename)
        with open(filePath, "w") as fd:
            fd.write(response.text)
    return response.json()


def StructureData(data):
    print("reading data for symbol: "+data["ticker"])
    results = []
    for entry in data["results"]:
        avgPrice = float(entry["vw"])
        openPrice = float(entry["o"])
        closePrice = float(entry["c"])
        trans = int(entry["n"])
        high = float(entry["h"])
        low = float(entry["l"])
        startTime = int(entry["t"])
        stopTime = startTime
        volume = int(entry["v"])

        results.append(PriceEntry(avgPrice, openPrice, closePrice, trans, high, low, volume, startTime, stopTime))
    return results

def CalculateMovingAverageBase(config):
    movingAverages = {}
    baseConfig = Config(config.Ticker, config.StartDate, config.StopDate, config.Units, config.Multiplier, config.ApiKey)
    baseConfig.Units = "day"
    baseConfig.Multiplier = 1

    baseDate = datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0) - timedelta(days = 1)
    date = baseDate - timedelta(days = MOVING_AVERAGE_LOOKBACK_DAYS)
    baseConfig.StartDate = date.strftime("%Y-%m-%d")
    baseConfig.StopDate = baseDate.strftime("%Y-%m-%d")

    print("calculating MA for date range: {} to {}".format(baseConfig.StartDate, baseConfig.StopDate))

    data = StructureData(FetchData(baseConfig))

    for ma in MOVING_AVERAGES_DAYS:
        if len(data) < ma:
            print("Not enough data to calculate {:n} day MA. Try adjust MOVING_AVERAGE_LOOKBACK_DAYS".format(ma))
            sys.exit(2)
        total = 0
        for entry in data[-ma:]:
            total = total + entry.AvgPrice
        movingAverages[ma] = total/ma
    
    return movingAverages

def sumPrices(prices):
    total = 0
    for price in prices:
        total += price.AvgPrice
    return total

def CalculateMovingAverageDataPoints(data, periodMinutes):
    windowSize = periodMinutes

    result = {}
    i = 0
    while i < len(data) - windowSize + 1:
        window = data[i:i+windowSize]
        dataPoint = sumPrices(window)/windowSize

        # x axis will be the time of the last data point in window
        time = window[-1].StartTime
        result[time] = dataPoint
        i += 1
    return result

def AnalyzeData(data, movingAverages):

    for ma in MOVING_AVERAGES_MINUTES:
        movingAverageDataPoints = CalculateMovingAverageDataPoints(data, ma)
        plt.plot(movingAverageDataPoints.keys(), movingAverageDataPoints.values(), label = "{:d} minute MA".format(ma))

    stockPrice = {}
    maDays = {}
    for price in data:
        stockPrice[price.StartTime] = price.AvgPrice
        for ma in MOVING_AVERAGES_DAYS:
            if ma not in maDays:
                maDays[ma] = {}
            maDays[ma][price.StartTime] = movingAverages[ma]
    
    # plot moving averages days
    for k,v in maDays.items():
        plt.plot(v.keys(), v.values(), label = "{:d} day MA".format(k))

    plt.plot(stockPrice.keys(), stockPrice.values(), label="SPY Price")
    plt.legend()
    plt.show()

config = ReadUserInput()
movingAverages = CalculateMovingAverageBase(config)

data = FetchData(config)
results = StructureData(data)
AnalyzeData(results, movingAverages)




