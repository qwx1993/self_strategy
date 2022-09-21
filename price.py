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
            # value_5m.to_csv('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_5m.csv" )

            # # 写入3m 
            # value_3m = rqdatac.get_price(vt_symbol_id, start_date=start_date, end_date=end_date, frequency='3m')[["open", "high", "low", "close"]] 
            # value_3m.to_csv('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_3m.csv" )

            # 写入1m 
            value_1m = rqdatac.get_price(vt_symbol_id, start_date=start_date, end_date=end_date, frequency='1m')[["open", "high", "low", "close"]] 
            value_1m.to_csv('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_1m.csv" )
            

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
            value_tick.to_csv('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_tick.csv" )