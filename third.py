# made by Haim

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

def re_buy():
    if is_btc:
        if origin_buy_price!=buy_price or origin_target_price!=target_price:
            return True
        else:
            return False
    else:
        return False

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time   

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price    

def price_setting():
    buy_price = get_balance(coin_ticker)
    buy_target = buy_price*buy_percent
    target_price = get_target_price(coin, k)
    origin_buy_price = buy_price
    origin_target_price = target_price
    current_price = get_current_price(coin)*get_balance(coin_ticker,coin_price=False)

    return buy_price,buy_target,target_price,origin_buy_price,origin_target_price,current_price
    
# -- Login
upbit = pyupbit.Upbit(infor.access, infor.secret)
print("Autotrade start")

# -- Coin Setting
coin = infor.sub_coin
coin_ticker = coin[4:]
print(coin)

# -- basic setting
minTrade = 5000
fee = 0.9995
origin_buy_price = get_balance(coin_ticker)
percent = infor.sub_tarK
buy_percent = infor.buy_percent
sub_can_buy = infor.sub_can_buy
origin_target_price = origin_buy_price*percent
error_cnt = 0
sellSeconds = infor.sellSeconds
k=infor.sub_k
limit_btc=infor.sub_limit_btc

target_price = get_target_price(coin, k)
buy_target = origin_buy_price*buy_percent

non_buy = True

# -- Start message
post_message("< %s Start _ third > %s autotrade started : percent = %.2f"%(str(datetime.datetime.now())[11:16],coin,(percent-1)*100))
post_message("Buy Price = %.1f, Target Price = %.1f, will buy price = %.1f"%(origin_buy_price, target_price, target_price*percent))

while True:
    try:
        # percent = infor.sub_tarK
        
        # Buy & Target Price
        buy_price = get_balance(coin_ticker)
        target_price = get_target_price(coin, k)
        is_btc = get_balance(coin_ticker,coin_price=False)>limit_btc

        # Re Buy
        if re_buy()==True:
            buy_price,buy_target,target_price,origin_buy_price,origin_target_price,current_price = price_setting()
            post_message("< Buy Checked _ third >")
            post_message("Buy Price = %.1f, Target Price = %.1f, Profitable = %.1f"%(buy_price, target_price, target_price-buy_price))

        time.sleep(1)

        # Current Price
        buy_price,buy_target,target_price,origin_buy_price,origin_target_price,current_price = price_setting()
        krw = get_balance("KRW",coin_price=False)
        current_coin_price = get_current_price(coin)

        # Sell : target_price < current_price
        if target_price*percent < current_coin_price and is_btc:
            post_message("Selling Time!! _ third")
            btc = get_balance(coin_ticker,coin_price=False)
            
            if btc > infor.limit_btc:
                sell_result = upbit.sell_market_order(coin, btc*fee)
                post_message("< Sell > %s : "%coin+"Buy Price = %.1f, Current Price = %.1f, Profitable = %.2f"%(buy_price, current_price, current_coin_price/target_price))
                post_message("KRW : %.1f"%(get_balance("KRW",coin_price=False)))

        now = datetime.datetime.now()
        start_time = get_start_time(coin)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=sellSeconds):

            target_price = get_target_price(coin, k)
            current_coin = get_balance(coin_ticker,coin_price=False)
            current_coin_price = get_current_price(coin)
            current_price = current_coin_price*current_coin
            
            print(target_price, current_coin_price)

            # Buy : buy_target > current_price
            if target_price > current_coin_price and non_buy:
                krw = get_balance("KRW",coin_price=False)
                if krw > 100000 and current_coin<(sub_can_buy/current_coin_price):
                    buy_result = upbit.buy_market_order(coin, sub_can_buy*fee)
                    non_buy = False
                    post_message("Buying time!! _ third")
                    
        else:
            btc = get_balance(coin_ticker,coin_price=False)
            non_buy = True
            if btc > limit_btc:
                sell_result = upbit.sell_market_order(coin, btc*fee)
                post_message("TimeOver Selling -- _ third")
                post_message("Profitable : %.3f percent"%(current_price/buy_price))
                post_message("KRW : %.1f"%(get_balance("KRW",coin_price=False)))

        time.sleep(1)

    except Exception as e:
        post_message("< Error _ third > "+str(e))
        error_cnt += 1
        time.sleep(1)

        if error_cnt>10:
            post_message("-- Overload --")
            break

# -- Finish message
post_message("< %s Finish > %s autotrade finished"%(str(datetime.datetime.now())[11:16],coin))
