from ast import Constant
import re
from time import sleep
from tkinter.tix import Tree
from vnpy_scripttrader import ScriptEngine
from vnpy.trader.constant import OrderType
from analysis import Analysis
from constants import Constants as Cons
import os
import time

def run(engine: ScriptEngine):
    """"""
    vt_symbols = ["sc2210.INE"]

    # 订阅行情
    engine.subscribe(vt_symbols)

    account_result = engine.get_account(vt_accountid="CTP.205187")
    engine.write_log(f"account_result => {account_result}")

    analysis = Analysis()

    # 持续运行，使用strategy_active来判断是否要退出程序
                # 进入程序
    now_date = time.strftime("%Y-%m-%d", time.localtime())
    temp_file = open("temp/temp-" + now_date, "w+")

    while engine.strategy_active:
        # 轮询获取行情
        for vt_symbol in vt_symbols:
            tick = engine.get_tick(vt_symbol)
            msg = f"最新行情, {tick} => {vt_symbol}"
            engine.write_log(msg)
            if tick is not None:
                analysis.analysis(tick, temp_file)
                if analysis.action_record is not None:
                    action = analysis.action_record['action']
                    if action == Cons.ACTION_OPEN_LONG:
                        result = engine.buy(vt_symbol=vt_symbol, price=tick.last_price, volume=1, order_type=OrderType.LIMIT)
                        engine.write_log(f"开多动作 => {result}")
                    elif action == Cons.ACTION_CLOSE_LONG:
                        result = engine.cover(vt_symbol=vt_symbol, price=tick.last_price, volume=1, order_type=OrderType.LIMIT)
                        engine.write_log(f"平多动作 => {result}")
                    elif action == Cons.ACTION_REVERSE_OPEN_LONG:
                        result = engine.buy(vt_symbol=vt_symbol, price=tick.last_price, volume=2, order_type=OrderType.LIMIT)
                        engine.write_log(f"逆趋势开多 => {result}")
                    elif action == Cons.ACTION_REVERSE_CLOSE_LONG:
                        result = engine.cover(vt_symbol=vt_symbol, price=tick.last_price, volume=2, order_type=OrderType.LIMIT)
                        engine.write_log(f"逆趋势平多 => {result}")
                    elif action == Cons.ACTION_OPEN_SHORT:
                        result = engine.short(vt_symbol=vt_symbol, price=tick.last_price, volume=1, order_type=OrderType.LIMIT)
                        engine.write_log(f"开空动作 => {result}")
                    elif action == Cons.ACTION_CLOSE_SHORT:
                        result = engine.sell(vt_symbol=vt_symbol, price=tick.last_price, volume=1, order_type=OrderType.LIMIT)
                        engine.write_log(f"逆趋势平多 => {result}")
                    elif action == Cons.ACTION_REVERSE_OPEN_SHORT:
                        result = engine.short(vt_symbol=vt_symbol, price=tick.last_price, volume=2, order_type=OrderType.LIMIT)
                        engine.write_log(f"逆趋势开空 => {result}")
                    elif action == Cons.ACTION_REVERSE_CLOSE_SHORT:
                        result = engine.sell(vt_symbol=vt_symbol, price=tick.last_price, volume=2, order_type=OrderType.LIMIT)
                        engine.write_log(f"逆趋势平空 => {result}")
                    # 重置记录  
                    analysis.action_record = None

        # 等待10秒进入下一轮
        sleep(10)
    
    # 将文件关闭
    temp_file.close


