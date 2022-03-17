import information as infor

import pyupbit
import requests
import time
import datetime

def post_message(text, token = infor.token, channel = infor.channel):
    """Slack message"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text})

def get_balance(ticker, coin_price=True):
    """balance check"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                if coin_price:
                    return float(b['balance'])*float(b['avg_buy_price'])
                else:
                    return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """current price"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]



# -- Login
upbit = pyupbit.Upbit(infor.access, infor.secret)
print("Autotrade start")

# -- Coin Setting
coin = infor.coin
coin_ticker = coin[4:]
print(coin)

# -- basic setting
minTrade = 5000
fee = 0.9995
origin_buy_price = get_balance(coin_ticker)
percent = infor.percent
error_cnt = 0

target_price = origin_buy_price*percent
# -- Start message
post_message("< %s Start > %s autotrade started"%(str(datetime.datetime.now())[11:16],coin))
post_message("Buy Price = %.1f, Target Price = %.1f, Profitable = %.1f"%(origin_buy_price, target_price, target_price-origin_buy_price))

while True:
    try:
        # Buy & Target Price
        buy_price = get_balance(coin_ticker)
        target_price = buy_price*percent
        is_btc = get_balance(coin_ticker,coin_price=False)>infor.limit_btc

        # Re Buy
        if origin_buy_price!=buy_price and is_btc:
            origin_buy_price = buy_price
            post_message("< Buy Checked >")
            post_message("Buy Price = %.1f, Target Price = %.1f, Profitable = %.1f"%(buy_price, target_price, target_price-buy_price))
        
        # Current Price
        current_price = get_current_price(coin)*get_balance(coin_ticker,coin_price=False)
        
        # Sell : target_price < current_price
        if target_price < current_price and is_btc:
            post_message("Selling Time!!")
            btc = get_balance(coin_ticker,coin_price=False)
            
            if btc > infor.limit_btc:
                sell_result = upbit.sell_market_order(coin, btc*fee)
                post_message("< Sell > %s : "%coin +str(sell_result))
                post_message("Buy Price = %.1f, Target Price = %.1f, Profitable = %.1f"%(buy_price, target_price, target_price-buy_price))

                current_price = get_current_price(coin)*get_balance(coin_ticker,coin_price=False)
                post_message("Profitable : %.2f %"%(current_price/buy_price))
                post_message("KRW : %.1f"%get_balance("KRW",coin_price=False))

        time.sleep(1)

    except Exception as e:
        post_message("< Error > "+str(e))
        error_cnt += 1
        time.sleep(1)

        if error_cnt>5:
            post_message("-- Overload --")
            break

# -- Finish message
post_message("< %s Finish > %s autotrade finished"%(str(datetime.datetime.now())[11:16],coin))