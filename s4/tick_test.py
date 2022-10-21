import sys
from types import SimpleNamespace
import logging
from sqlalchemy import true 
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
    close_price_by_l = None # 通过l_price去平仓
    close_price = None
    open_price = None # 开仓价格
    agreement_close_price = None
    # 定义参数
    hand_number = 1
    trade_action = None 
    is_new_minute = None # 上一分钟
    last_tick_list = []
    actions = [] # 交易动作
    unit_value = None

    # 添加参数和变量名到对应的列表
    def __init__(self, vt_symbol, unit_value):
        """"""
        self.vt_symbol = vt_symbol
        self.unit_value = unit_value

        """
        初始化日志
        """
        file.init_log(self.vt_symbol)
        logging.info(self.vt_symbol)
        self.history = History()
        self.tick_list = []
        self.last_tick_list = []
        self.actions = []
        # 追溯当天数据
        # price = Price()
        # order_id = vt_symbol.upper()

        # now_date = datetime.datetime.now()
        # hour = now_date.hour
        # if hour > 15:
        #     d_format = (now_date + timedelta(days=1)).strftime("%Y%m%d")
        # else:
        #     d_format = now_date.strftime("%Y%m%d")
        # history_list = price.get_price(order_id, d_format, d_format)
        # if len(history_list) > 0:
        #     for cd in history_list:
        #         self.history.realtime_analysis_for_cd(cd)

    """
    通过该函数收到Tick推送。
    """     
    def on_tick(self, tick):
        self.save_current_tick(tick)
        tick_obj = self.get_tick_object(tick)
        minute_cd = TickLogic.merge_ticks_to_m1(self.tick_list)
        last_minute_cd = TickLogic.merge_ticks_to_m1(self.last_tick_list)
        if self.is_new_minute and last_minute_cd is not None:
            self.on_bar(last_minute_cd)
        if minute_cd is not None:
            instance = self.get_history_instance()
            instance.realtime_analysis_for_cd(minute_cd)
            if self.trade_action is None and trade.simulation_can_open_a_position(self.vt_symbol, tick):
                # 出现ml并且当前一分钟没有刷新l
                if self.history.ml is not None and self.history.extremum_l_price is not None and self.history.extremum_l_price == instance.extremum_l_price:
                    # if S4Tick.open_a_price(instance.breakthrough_direction, self.history.last_cd, tick_obj) and self.can_open_a_position_by_max_limit() and self.open_by_beyond_max_unit_value():
                    if S4Tick.open_a_price(instance.breakthrough_direction, self.history.last_cd, tick_obj) and self.open_by_beyond_max_unit_value():
                    # if S4Tick.open_a_price(instance.breakthrough_direction, self.history.last_cd, tick_obj):
                        if instance.breakthrough_direction == Cons.DIRECTION_UP:
                            # result = self.buy(tick.current, self.hand_number)
                            self.add_action(tick, Cons.ACTION_OPEN_LONG, tick.current + self.unit_value)
                            self.open_price = tick.current + self.unit_value
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:long => max_amplitude:{self.history.max_amplitude} =>  ml:{self.history.ml} => l: {self.history.extremum_l} => l_price:{self.history.extremum_l_price} => last_cd:{self.history.last_cd} => history_dirction:{self.history.breakthrough_direction} agreement_extre_l => {self.history.agreement_extremum_l}")
                            self.trade_action = Cons.ACTION_CLOSE_LONG 
                            # 设置一个平仓价格
                            # self.close_price = self.history.last_cd.low
                            # 使用l_price作为平仓价
                            self.close_price = self.history.agreement_extremum_l_price
                            # 使用l_price作为平仓价  
                            self.close_price_by_l = self.history.agreement_extremum_l_price
                            # 增加开仓统计次数
                            self.add_open_a_position_times()  
                        elif instance.breakthrough_direction == Cons.DIRECTION_DOWN:
                            # result = self.short(tick.current, self.hand_number)
                            self.add_action(tick, Cons.ACTION_OPEN_SHORT, tick.current - self.unit_value)
                            self.open_price = tick.current - self.unit_value
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:short => max_amplitude:{self.history.max_amplitude} =>  ml:{self.history.ml} => l: {self.history.extremum_l} => l_price:{self.history.extremum_l_price} => last_cd:{self.history.last_cd} => history_dirction:{self.history.breakthrough_direction} agreement_extre_l => {self.history.agreement_extremum_l}")
                            self.trade_action = Cons.ACTION_CLOSE_SHORT
                            # 设置一个平仓价格
                            # self.close_price = self.history.last_cd.high
                            # 使用l_price作为平仓价
                            self.close_price = self.history.agreement_extremum_l_price
                            # 使用l_price作为平仓价
                            self.close_price_by_l = self.history.agreement_extremum_l_price
                            # 增加开仓统计次数
                            self.add_open_a_position_times() 
            elif self.trade_action == Cons.ACTION_CLOSE_LONG: # 止损
                if self.close_by_same_minute(tick):
                    if S4Tick.close_a_price(self.trade_action, self.close_price_by_l, tick_obj):
                        self.add_action(tick, Cons.ACTION_CLOSE_LONG, tick.current - self.unit_value)
                        logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:long_l => close_price_by_l:{self.close_price_by_l} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price}")
                        self.trade_action = None
                        self.reset_price()
                        # 重新设置ml
                        self.reset_history_ml()
                elif S4Tick.close_a_price(self.trade_action, self.close_price, tick_obj) or trade.simulation_need_close_position(self.vt_symbol, tick):
                    # result = self.sell(tick.current, self.hand_number)
                    self.add_action(tick, Cons.ACTION_CLOSE_LONG, tick.current - self.unit_value)
                    logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:long => close_price:{self.close_price} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price}")
                    self.trade_action = None
                    self.reset_price()
                    # 重新设置ml
                    self.reset_history_ml()
                elif self.is_exceed_last_cd_high(tick):
                    self.set_agreement_close_price_by_long(tick)
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_agreement_close_price_by_long => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
                elif self.is_exceed_last_cd_low(tick):
                    self.set_close_price_by_agreement()
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_close_price_by_agreement => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                if self.close_by_same_minute(tick):
                    if S4Tick.close_a_price(self.trade_action, self.close_price_by_l, tick_obj):
                        self.add_action(tick, Cons.ACTION_CLOSE_SHORT, tick.current + self.unit_value)
                        logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:short_l => close_price_by_l:{self.close_price_by_l} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price}")
                        self.trade_action = None
                        self.reset_price()
                        # 重新设置ml
                        self.reset_history_ml()
                elif S4Tick.close_a_price(self.trade_action, self.close_price, tick_obj) or trade.simulation_need_close_position(self.vt_symbol, tick):
                    
                    # result = self.cover(tick.current, self.hand_number)
                    self.add_action(tick, Cons.ACTION_CLOSE_SHORT, tick.current + self.unit_value)
                    logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:short => close_price:{self.close_price} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price}")
                    self.trade_action = None
                    self.reset_price()
                    # 重新设置ml
                    self.reset_history_ml()
                elif self.is_exceed_last_cd_high(tick):
                    self.set_agreement_close_price_by_short(tick)
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_agreement_close_price_by_short => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
                elif self.is_exceed_last_cd_low(tick):
                    self.set_close_price_by_agreement()
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_close_price_by_agreement => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")

            # 删除实例
            self.del_history_instance(instance)

    """
    通过该函数收到新的1分钟K线推送。
    """
    def on_bar(self, cd):
        # 实时统计分钟线的情况
        self.history.realtime_analysis_for_cd(cd)
    
    """
    获取tick对象
    """
    def get_tick_object(self, tick):
        cd = SimpleNamespace()
        cd.datetime = tick.datetime
        cd.current = tick.current
        return cd

    """
    保存当前一分钟的tick数据
    """
    def save_current_tick(self, cd):
       
        if len(self.tick_list) == 0:
            self.is_new_minute = False
            self.tick_list.append(cd)
        else:
            first_datetime = self.tick_list[0].datetime
            # 不是同一分钟的
            if not cd.datetime.minute == first_datetime.minute:
                # 重新刷新
                self.is_new_minute = True
                self.last_tick_list = self.tick_list
                self.tick_list = []
                self.tick_list.append(cd)
            else:
                self.is_new_minute = False
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
    def is_exceed_last_cd_high(self, tick):
        if self.trade_action == Cons.ACTION_CLOSE_LONG:
            if tick.current < self.history.last_cd.low:
                return True
        elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
            if tick.current > self.history.last_cd.high:
                return True
        return False

    """
    开多情况，如果比上一分钟的高点高为真
    开空情况，如果比上一分钟的低点低为真
    """
    def is_exceed_last_cd_low(self, tick):
        if self.trade_action == Cons.ACTION_CLOSE_LONG:
            if tick.current > self.history.last_cd.high:
                return True
        elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
            if tick.current < self.history.last_cd.low:
                return True
        return False
    
    """
    开多设置协定平仓价
    """
    def set_agreement_close_price_by_long(self, tick):
        if self.agreement_close_price is None or tick.current < self.agreement_close_price:
            self.agreement_close_price = tick.current

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
    def set_agreement_close_price_by_short(self, tick):
        if self.agreement_close_price is None or tick.current > self.agreement_close_price:
            self.agreement_close_price = tick.current
    
    """
    重置价格
    """
    def reset_price(self):
        self.close_price = None
        self.agreement_close_price = None

    """
    写入交易动作
    """ 
    def add_action(self, cd, action, price):
        record = {
            "price": price,
            "action": action,
            "datetime": cd.datetime
        }

        self.actions.append(record)
    
    """
    每次开仓记录开仓次数
    """
    def add_open_a_position_times(self):
        self.history.has_open_a_position_times += 1
    
    """
    判断是否超过最大允许开仓次数
    """
    def can_open_a_position_by_max_limit(self):
        if self.history.has_open_a_position_times < self.history.max_limit:
            return True
        else:
            return False

    """
    判断同一分钟是否可以平仓
    """
    def close_by_same_minute(self, tick):
        open_minute = self.actions[-1]['datetime'].minute
        if tick.datetime.minute == open_minute:
            return True

        # if self.trade_action == Cons.ACTION_CLOSE_LONG:
        #     if tick.current < self.close_price_by_l:
        #         return True
        # elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
        #     if tick.current > self.close_price_by_l:
        #         return True
        return False
    
    """
    重新设置ml为None
    """
    def reset_history_ml(self):
        self.history.ml = None
        self.history.agreement_extremum_l = None
        self.history.agreement_extremum_l_price = None

    """
    是否为赢得状态
    """
    def is_win_point(self, tick):
        if self.trade_action == Cons.ACTION_CLOSE_LONG:
            if tick.current - self.open_price > self.unit_value:
                return true
        elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
            if self.open_price - tick.current > self.unit_value:
                return true
        return False
    
    """
    获取平常价格
    """
    def get_close_price_by_win_point(self, tick):
        if self.is_win_point(tick):
            return self.close_price
        else:
            return self.close_price_by_l
    
    """
    d跟l的间距要超过限定个数单位才能开仓
    """
    def open_by_beyond_max_unit_value(self):
        extremum_d_price = self.history.extremum_d_price
        extremum_l_price = self.history.extremum_l_price
        if extremum_d_price is not None and extremum_l_price is not None:
            if abs(extremum_d_price - extremum_l_price) > 30 * self.unit_value:
                return True
        
        return False