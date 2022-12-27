import string
import sys
from types import SimpleNamespace
import os
import copy
import datetime
from self_strategy.constants import Constants
from self_strategy.logic import Logic
import rqdatac
from datetime import timedelta

class Price:

        def __init__(self):
        # 所有的list数据需要初始化
            rqdatac.init(username=Constants.RQDATA_USERNAME, password=Constants.RQDATA_PASSWORD)

        """
        保存1m、3m、5m的历史行情数据
        """
        def save_prices_csv(self, vt_symbol, days):
            d1 = datetime.datetime.now()
            start_date = Logic.get_date_str(d1, -days)
            end_date = Logic.get_date_str(d1, -1)
            # print(f"vt_symbol => {vt_symbol}")
            # 写入5m 
            vt_symbol_id = rqdatac.id_convert(vt_symbol)
      
            # value_5m = rqdatac.get_price(vt_symbol_id, start_date=start_date, end_date=end_date, frequency='5m')[["open", "high", "low", "close"]]
            # value_5m.to_csv('C:/Users/king/strategies/data/' + f"{vt_symbol}_5m.csv" )

            # # 写入3m 
            # value_3m = rqdatac.get_price(vt_symbol_id, start_date=start_date, end_date=end_date, frequency='3m')[["open", "high", "low", "close"]] 
            # value_3m.to_csv('C:/Users/king/strategies/data/' + f"{vt_symbol}_3m.csv" )

            # 写入1m 
            print(vt_symbol_id)
            value_1m = rqdatac.get_price(vt_symbol_id, start_date=start_date, end_date=end_date, frequency='1m')[["open", "high", "low", "close"]] 
            value_1m.to_csv('C:/Users/king/strategies/data/' + f"{vt_symbol}_1m.csv" )
            

        """
        保存十天的tick数据
        """
        def save_tick_prices_csv(self, vt_symbol, days):
            d1 = datetime.datetime.now()
            start_date = Logic.get_date_str(d1, -days)
            end_date = Logic.get_date_str(d1, -1)
            # print(f"vt_symbol => {vt_symbol}")
            # 写入tick
            vt_symbol = rqdatac.id_convert(vt_symbol)
      
            value_tick = rqdatac.get_price(vt_symbol, start_date=start_date, end_date=end_date, frequency='tick')[["last"]]
            value_tick.to_csv('C:/Users/king/strategies/data_tick/' + f"{vt_symbol}_tick.csv" )

        """
        保存主力合约的数据
        """        
        def  save_dominant_price(self, underlying_symbols, days):
            d1 = datetime.datetime.now()
            start_date = Logic.get_date_str(d1, -days)
            end_date = Logic.get_date_str(d1, -1)
            print(f"参数 => underlying_symbols:{underlying_symbols} => start_date:{start_date} => end_date:{end_date}")
            value_1m = rqdatac.futures.get_dominant_price(underlying_symbols, start_date=start_date, end_date=end_date, frequency='1m')[["open", "high", "low", "close"]] 
            value_1m.to_csv('C:/Users/king/strategies/data/' + f"{underlying_symbols}_dominant_{days}_1m.csv" )
        
        """
        保存主力合约tick数据
        """
        def  save_dominant_tick_price(self, underlying_symbols, days):
            d1 = datetime.datetime.now()
            start_date = Logic.get_date_str(d1, -days)
            end_date = Logic.get_date_str(d1, -1)
            print(f"参数 => underlying_symbols:{underlying_symbols} => start_date:{start_date} => end_date:{end_date}")
            value_1m = rqdatac.futures.get_dominant_price(underlying_symbols, start_date=start_date, end_date=end_date, frequency='tick', adjust_type='none')[["last"]] 
            value_1m.to_csv('C:/Users/king/strategies/data_tick/' + f"{underlying_symbols}_dominant_{days}_tick.csv" )
        
        """
        下载指定日期的tick合约数据
        """
        def save_appoint_dominant_tick_price(self, underlying_symbols, start_date, end_date):
            print(f"参数 => underlying_symbols:{underlying_symbols} => start_date:{start_date} => end_date:{end_date}")
            value_1m = rqdatac.futures.get_dominant_price(underlying_symbols, start_date=start_date, end_date=end_date, frequency='tick', adjust_type='none')[["last"]] 
            value_1m.to_csv('C:/Users/king/strategies/data_tick/' + f"{underlying_symbols}_dominant_test_tick.csv" )

        """
        保存当天合约数据保存到csv中
        """ 
        def save_same_day_price(self, vt_symbol, start_date, end_date):
            vt_symbol = rqdatac.id_convert(vt_symbol)
            value_1m = rqdatac.get_price(vt_symbol, start_date=start_date, end_date=end_date, frequency='1m', expect_df=True)[[ "open", "high", "low", "close"]] 
            value_1m.to_csv('C:/Users/king/strategies/data/' + f"{vt_symbol}_same_day_1m.csv" )

        """
        获取当天数据，转化成自定义格式
        """
        def get_price(self, vt_symbol, start_date, end_date):
            vt_symbol = rqdatac.id_convert(vt_symbol)
            ls = []
            prices = rqdatac.get_price(vt_symbol, start_date=start_date, end_date=end_date, frequency='1m', expect_df=True)[[ "open", "high", "low", "close"]] 
            for index, row in prices.iterrows():
                opening_price = float(row['open'])
                closing_price = float(row['close'])
                high = float(row['high'])
                low = float(row['low'])

                current = SimpleNamespace()
                current.datetime = str(index[1])
                current.flunc = round(abs(closing_price - opening_price), 2)
                current.open = opening_price
                current.close = closing_price
                current.high = high
                current.low = low
                current.direction = Logic.get_direction_value(opening_price, closing_price)
                ls.append(current)
            
            return ls

        """
        获取最近一分钟的数据
        """   
        def current_minute_close(self, vt_symbol:string):
            vt_symbol = vt_symbol.upper()
            vt_symbol = rqdatac.id_convert(vt_symbol)
            current_minute = rqdatac.current_minute(vt_symbol)
            return current_minute['close'][0]