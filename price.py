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
        def save_10_days_prices_csv(self, vt_symbol):
            d1 = datetime.datetime.now()
            start_date = Logic.get_date_str(d1, -10)
            end_date = Logic.get_date_str(d1, -1)
            # 写入5m 
            value_5m = rqdatac.get_price(vt_symbol, start_date=start_date, end_date=end_date, frequency='5m')
            value_5m.to_csv('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_5m.csv" )

            # 写入3m 
            value_3m = rqdatac.get_price(vt_symbol, start_date=start_date, end_date=end_date, frequency='3m')
            value_3m.to_csv('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_3m.csv" )

            # 写入1m 
            value_1m = rqdatac.get_price(vt_symbol, start_date=start_date, end_date=end_date, frequency='1m')
            value_1m.to_csv('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_1m.csv" )