import sys
from types import SimpleNamespace
import logging 
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

from self_strategy.constants import Constants as Cons
from self_strategy.s4.minute import Minute as History
from self_strategy.tick_logic import TickLogic
from self_strategy.s4.tick import Tick as S4Tick
from self_strategy.utils import (
    file,
    trade
)
from copy import deepcopy
import time
import os
from self_strategy.price import Price
import datetime
from datetime import timedelta

# tick 数据测试
class TickTest():
    vt_symbol = None
    history = None
    tick_list = []
    close_price = None
    agreement_close_price = None
    # 定义参数
    hand_number = 1
    trade_action = None 

    # 添加参数和变量名到对应的列表
    def __init__(self, vt_symbol):
        """"""
        self.vt_symbol = vt_symbol

        """
        初始化日志
        """
        file.init_log(self.vt_symbol)
        logging.info(self.vt_symbol)
        self.history = History()

        # 追溯当天数据
        price = Price()
        order_id = vt_symbol.upper()

        now_date = datetime.datetime.now()
        hour = now_date.hour
        if hour > 15:
            d_format = (now_date + timedelta(days=1)).strftime("%Y%m%d")
        else:
            d_format = now_date.strftime("%Y%m%d")
        history_list = price.get_price(order_id, d_format, d_format)
        if len(history_list) > 0:
            for cd in history_list:
                self.history.realtime_analysis_for_cd(cd)

    """
    通过该函数收到Tick推送。
    """     
    def on_tick(self, tick):
        self.save_current_tick(tick)
        minute_cd = TickLogic.merge_ticks_to_m1(self.tick_list)
        if minute_cd is not None:
            instance = self.get_history_instance()
            instance.realtime_analysis_for_cd(minute_cd)
            if self.trade_action is None and trade.can_open_a_position(self.vt_symbol):
                # 出现ml并且当前一分钟没有刷新l
                if self.history.ml is not None and self.history.extremum_l_price == instance.extremum_l_price:
                    if S4Tick.open_a_price(instance.breakthrough_direction, self.history.last_cd, tick_obj):
                        if instance.breakthrough_direction == Cons.DIRECTION_UP:
                            result = self.buy(tick.last_price, self.hand_number)
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:long => max_amplitude:{self.history.max_amplitude} =>  ml:{self.history.ml} => l: {self.history.extremum_l} => l_price:{self.history.extremum_l_price} => last_cd:{self.history.last_cd} => history_dirction:{self.history.breakthrough_direction}")
                            self.trade_action = Cons.ACTION_CLOSE_LONG 
                            # 设置一个平仓价格
                            self.close_price = self.history.last_cd.low  
                        elif instance.breakthrough_direction == Cons.DIRECTION_DOWN:
                            result = self.short(tick.last_price, self.hand_number)
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:short => max_amplitude:{self.history.max_amplitude} =>  ml:{self.history.ml} => l: {self.history.extremum_l} => l_price:{self.history.extremum_l_price} => last_cd:{self.history.last_cd} => history_dirction:{self.history.breakthrough_direction}")
                            self.trade_action = Cons.ACTION_CLOSE_SHORT
                            # 设置一个平仓价格
                            self.close_price = self.history.last_cd.high
            elif self.trade_action == Cons.ACTION_CLOSE_LONG: # 止损
                if S4Tick.close_a_price(self.trade_action, self.close_price, tick_obj) or trade.need_close_position(self.vt_symbol):
                    
                    result = self.sell(tick.last_price, self.hand_number)

                    logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:long => close_price:{self.close_price} =>  tick_price:{tick.last_price} => agreement_close_price:{self.agreement_close_price}")
                    self.trade_action = None
                    self.reset_price()
                elif self.is_exceed_last_cd_high(tick):
                    self.set_agreement_close_price_by_long(tick)
                    logging.info(f"vt_symbol:{self.vt_symbol} => set_agreement_close_price_by_long => tick_last_price:{tick.last_price} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
                elif self.is_exceed_last_cd_low(tick):
                    self.set_close_price_by_agreement()
                    logging.info(f"vt_symbol:{self.vt_symbol} => set_close_price_by_agreement => tick_last_price:{tick.last_price} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                if S4Tick.close_a_price(self.trade_action, self.close_price, tick_obj) or trade.need_close_position(self.vt_symbol):
                    
                    result = self.cover(tick.last_price, self.hand_number)
                    
                    logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:short => close_price:{self.close_price} =>  tick_price:{tick.last_price} => agreement_close_price:{self.agreement_close_price}")
                    self.trade_action = None
                    self.reset_price()
                elif self.is_exceed_last_cd_high(tick):
                    self.set_agreement_close_price_by_short(tick)
                    logging.info(f"vt_symbol:{self.vt_symbol} => set_agreement_close_price_by_short => tick_last_price:{tick.last_price} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
                elif self.is_exceed_last_cd_low(tick):
                    self.set_close_price_by_agreement()
                    logging.info(f"vt_symbol:{self.vt_symbol} => set_close_price_by_agreement => tick_last_price:{tick.last_price} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")

            # 删除实例
            self.del_history_instance(instance)

    """
    通过该函数收到新的1分钟K线推送。
    """
    def on_bar(self, cd):
        # 实时统计分钟线的情况
        self.history.realtime_analysis_for_cd(cd)
   
    def on_order(self, order: OrderData):
        """
        通过该函数收到委托状态更新推送。
        """
        pass


    def on_trade(self, trade: TradeData):
        """
        通过该函数收到成交推送。
        """
        # 成交后策略逻辑仓位发生变化，需要通知界面更新。
        self.put_event()


    def on_stop_order(self, stop_order: StopOrder):
        """
        通过该函数收到本地停止单推送。
        """
        pass
    
    """
    获取tick对象
    """
    def get_tick_object(self, tick:TickData):
        cd = SimpleNamespace()
        cd.datetime = tick.datetime
        cd.current = tick.last_price
        return cd

    """
    保存当前一分钟的tick数据
    """
    def save_current_tick(self, cd):
       
        if len(self.tick_list) == 0:
            self.tick_list.append(cd)
        else:
            first_datetime = self.tick_list[0].datetime
            # 不是同一分钟的
            if not cd.datetime.minute == first_datetime.minute:
                self.tick_list = []
                self.tick_list.append(cd)
            else:
                self.tick_list.append(cd)

    """
    获取一个新的实例变量
    """
    def get_history_instance(self):
        new_history = deepcopy(self.history) 
        return new_history
    
    """
    销毁一个实例
    """
    def del_history_instance(self, history):
        del history

    """
    开多情况，如果比上一分钟的低点低为真
    开空情况，如果比上一分钟的高点高为真
    """
    def is_exceed_last_cd_high(self, tick:TickData):
        if self.trade_action == Cons.ACTION_CLOSE_LONG:
            if tick.last_price < self.history.last_cd.low:
                return True
        elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
            if tick.last_price > self.history.last_cd.high:
                return True
        return False

    """
    开多情况，如果比上一分钟的高点高为真
    开空情况，如果比上一分钟的低点低为真
    """
    def is_exceed_last_cd_low(self, tick:TickData):
        if self.trade_action == Cons.ACTION_CLOSE_LONG:
            if tick.last_price > self.history.last_cd.high:
                return True
        elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
            if tick.last_price < self.history.last_cd.low:
                return True
        return False
    
    """
    开多设置协定平仓价
    """
    def set_agreement_close_price_by_long(self, tick:TickData):
        if self.agreement_close_price is None or tick.last_price < self.agreement_close_price:
            self.agreement_close_price = tick.last_price

    """
    设置开仓协定价格
    """
    def set_close_price_by_agreement(self):
        if self.agreement_close_price is not None:
            self.close_price = self.agreement_close_price
            self.agreement_close_price = None

    """
    开空设置协定平仓价
    """
    def set_agreement_close_price_by_short(self, tick:TickData):
        if self.agreement_close_price is None or tick.last_price > self.agreement_close_price:
            self.agreement_close_price = tick.last_price
    
    """
    重置价格
    """
    def reset_price(self):
        self.close_price = None
        self.agreement_close_price = None
