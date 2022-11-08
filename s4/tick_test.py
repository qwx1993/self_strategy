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
from self_strategy.s4.fixed_minute import FixedMinute
from self_strategy.tick_logic import TickLogic
from self_strategy.s4.tick import Tick as S4Tick
from self_strategy.logic import Logic
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
    instance_1 = None # 实例1
    tick_list = []
    close_price_by_lose = None # 止损价位
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
    open_type = 1 # 开仓类型
    interval_datetime = None #开仓间隔
    interval_minutes = 15 # 开仓间隔15分钟
    opportunity_number = 0 # 亏损后允许重开的机会
    opportunity_number_limit = 2

    first_interval_minutes = 15 # 第一次开仓的间隔时间
    second_interval_minutes = 10 # 第二次开仓的间隔时间
    d_win_flag = False # D开仓并且止盈的标记
    d_win_number = 0 # 左侧策略开仓赢次数
    d_win_number_limit = 1 # 左侧赢多少次进入右侧策略
    last_open_d_datetime = None # 最后
    last_open_d = None 

    l_interval_datetime = None #开仓间隔 
    l_interval_minutes = 15 # 开仓间隔15分钟
    l_first_interval_minutes = 15 # L第一次开仓得时间间隔
    l_second_interval_minutes = 10 # L第二次开仓的间隔时间
    l_opportunity_number = 0 # 亏损后允许重开的机会
    l_opportunity_number_limit = 2

    start_list = [] # 起点记录
    complete_start_list = [] # 真实得分钟记录
    instance_1_open_number = 0 # 开仓次数
    instance_1_open_win_number = 0 # 赢得次数
    instance_1_open_win_number_limit = 3 # 赢开仓次数限制 默认3次
    instance_1_open_number_limit = 2000 # 开仓次数限制

    # 添加参数和变量名到对应的列表
    def __init__(self, vt_symbol, unit_value, win_number_limit):
        """"""
        self.vt_symbol = vt_symbol
        self.unit_value = unit_value
        self.instance_1_open_win_number_limit = win_number_limit

        """
        初始化日志
        """
        file.init_log(self.vt_symbol)
        logging.info(self.vt_symbol)
        self.history = History()
        self.tick_list = []
        self.last_tick_list = []
        self.actions = []

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
            if self.trade_action is None and trade.simulation_can_open_a_position(self.vt_symbol, tick):
                # 出现ml并且当前一分钟没有刷新l
                direction = self.history.breakthrough_direction
                if (not self.d_win_flag) and S4Tick.open_a_price_by_agreement(direction, self.history.extremum_d, self.history.agreement_extremum_d, self.history.last_cd, tick_obj) and self.history.change_direction_number >= 1:
                    # 时间间隔起点
                    if self.interval_datetime is None:
                        self.interval_datetime = self.history.agreement_extremum_d.appoint_datetime
                    if Logic.within_minutes(self.interval_minutes, self.interval_datetime, minute_cd.datetime) and self.has_opportunity(Cons.OPEN_BY_D):
                        if self.history.breakthrough_direction == Cons.DIRECTION_UP:
                            # result = self.short(tick.current, self.hand_number)
                            self.add_action(tick, Cons.ACTION_OPEN_SHORT, tick.current - self.unit_value)
                            self.open_price = tick.current - self.unit_value
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:short_by_d => max_amplitude:{self.history.max_amplitude} =>  tick:{tick.current} => l: {self.history.extremum_l} => l_price:{self.history.extremum_l_price} => last_cd:{self.history.last_cd} => history_dirction:{self.history.breakthrough_direction} agreement_extremum_d => {self.history.agreement_extremum_d} d=> {self.history.extremum_d} opportunity => {self.opportunity_number} change_direction_number => {self.history.change_direction_number}")
                            self.trade_action = Cons.ACTION_CLOSE_SHORT
                            self.close_price = self.history.extremum_d_price
                            self.close_price_by_lose = self.history.extremum_d_price
                            self.open_type = Cons.OPEN_BY_D
                            self.last_open_d_datetime = self.history.extremum_d.datetime
                            self.last_open_d = self.history.extremum_d
                            self.increase_opportunity_number()
                            self.after_open_a_position()
                        elif self.history.breakthrough_direction == Cons.DIRECTION_DOWN:
                            # result = self.buy(tick.current, self.hand_number)
                            self.add_action(tick, Cons.ACTION_OPEN_LONG, tick.current + self.unit_value)
                            self.open_price = tick.current + self.unit_value
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:long_by_d => max_amplitude:{self.history.max_amplitude} =>  tick:{tick.current} => l: {self.history.extremum_l} => l_price:{self.history.extremum_l_price} => last_cd:{self.history.last_cd} => history_dirction:{self.history.breakthrough_direction} agreement_extremum_d => {self.history.agreement_extremum_d}  d=> {self.history.extremum_d} opportunity => {self.opportunity_number} change_direction_number => {self.history.change_direction_number}")
                            self.trade_action = Cons.ACTION_CLOSE_LONG 
                            # 使用l_price作为平仓价
                            self.close_price = self.history.extremum_d_price
                            # 使用l_price作为平仓价  
                            self.close_price_by_lose = self.history.extremum_d_price
                            self.open_type = Cons.OPEN_BY_D
                            self.last_open_d_datetime = self.history.extremum_d.datetime
                            self.last_open_d = self.history.extremum_d
                            self.increase_opportunity_number()
                            self.after_open_a_position()
                elif self.d_win_flag and self.instance_1 is not None  and self.has_opportunity_by_instance_1_win():
                    direciton1 = self.instance_1.breakthrough_direction
                    # if tick.datetime.day == 19 and tick.datetime.hour == 0 and tick.datetime.minute == 1:
                    #     print(f"ddddddd {tick.datetime} {tick.current} {self.instance_1.extremum_d_price} d => {self.instance_1.extremum_d} =>l {self.instance_1.extremum_l_price} {S4Tick.open_a_position_by_price(direciton1, self.instance_1.extremum_d_price, tick_obj)} direciton1 => {direciton1}")
                    if self.instance_1.extremum_d_price is not None and self.instance_1.extremum_l_price is not None and S4Tick.open_a_position_by_price(direciton1, self.instance_1.extremum_d_price, tick_obj):
                        if direciton1 == Cons.DIRECTION_UP:
                            # result = self.buy(tick.current, self.hand_number)
                            self.add_action(tick, Cons.ACTION_OPEN_LONG, tick.current + self.unit_value)
                            self.open_price = tick.current + self.unit_value
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:long_by_instance_1   =>  tick1:{tick.current} => l: {self.instance_1.extremum_l} => l_price:{self.instance_1.extremum_l_price} => last_cd1:{self.instance_1.last_cd} => history_dirction1:{direciton1}  d1=> {self.instance_1.extremum_d} d_price => {self.instance_1.extremum_d_price}")
                            self.trade_action = Cons.ACTION_CLOSE_LONG 
                            # 使用l_price作为平仓价
                            self.close_price = self.instance_1.extremum_l_price
                            self.close_price_by_lose = self.instance_1.extremum_l_price
                            self.increase_opportunity_number_by_instance_1()
                        elif direciton1 == Cons.DIRECTION_DOWN:
                            # result = self.short(tick.current, self.hand_number)
                            self.add_action(tick, Cons.ACTION_OPEN_SHORT, tick.current - self.unit_value)
                            self.open_price = tick.current - self.unit_value
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:short_by_instance_1 =>  tick1:{tick.current} => l: {self.instance_1.extremum_l} => l_price:{self.instance_1.extremum_l_price} => last_cd1:{self.instance_1.last_cd} => history_dirction1:{direciton1}  d1=> {self.instance_1.extremum_d}  d_price => {self.instance_1.extremum_d_price}")
                            self.trade_action = Cons.ACTION_CLOSE_SHORT
                            self.close_price = self.instance_1.extremum_l_price
                            self.close_price_by_lose = self.instance_1.extremum_l_price
                            self.increase_opportunity_number_by_instance_1()
            elif self.trade_action == Cons.ACTION_CLOSE_LONG:
                if self.close_by_same_minute(tick):
                    if S4Tick.close_a_price(self.trade_action, self.close_price_by_lose, tick_obj):
                        self.add_action(tick, Cons.ACTION_CLOSE_LONG, tick.current - self.unit_value)
                        logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:long_l => close_price_by_lose:{self.close_price_by_lose} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price}")
                        self.after_close(tick_obj)
                elif S4Tick.close_a_price(self.trade_action, self.get_close_price_by_win_point(tick), tick_obj) or trade.simulation_need_close_position(self.vt_symbol, tick):
                    # result = self.sell(tick.current, self.hand_number)
                    self.add_action(tick, Cons.ACTION_CLOSE_LONG, tick.current - self.unit_value)
                    logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:long => close_price:{self.close_price} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price}")
                    self.after_close(tick_obj)
                elif self.is_exceed_last_cd_high(tick):
                    self.set_agreement_close_price_by_long(tick)
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_agreement_close_price_by_long => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
                elif self.is_exceed_last_cd_low(tick):
                    self.set_close_price_by_agreement()
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_close_price_by_agreement => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                if self.close_by_same_minute(tick):
                    if S4Tick.close_a_price(self.trade_action, self.close_price_by_lose, tick_obj):
                        self.add_action(tick, Cons.ACTION_CLOSE_SHORT, tick.current + self.unit_value)
                        logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:short_l => close_price_by_lose:{self.close_price_by_lose} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price}  open_price => {self.open_price} close_price_by_lose => {self.close_price_by_lose}")
                        self.after_close(tick_obj)
                elif S4Tick.close_a_price(self.trade_action, self.get_close_price_by_win_point(tick), tick_obj) or trade.simulation_need_close_position(self.vt_symbol, tick):
                    
                    # result = self.cover(tick.current, self.hand_number)
                    self.add_action(tick, Cons.ACTION_CLOSE_SHORT, tick.current + self.unit_value)
                    logging.info(f"vt_symbol:{self.vt_symbol} => close_direction:short => close_price:{self.close_price} =>  tick_price:{tick.current} => agreement_close_price:{self.agreement_close_price} open_price => {self.open_price} close_price_by_lose => {self.close_price_by_lose}")
                    self.after_close(tick_obj)
                elif self.is_exceed_last_cd_high(tick):
                    self.set_agreement_close_price_by_short(tick)
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_agreement_close_price_by_short => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
                elif self.is_exceed_last_cd_low(tick):
                    self.set_close_price_by_agreement()
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_close_price_by_agreement => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")

            # 删除实例
            # self.del_history_instance(instance)

    """
    通过该函数收到新的1分钟K线推送。
    """
    def on_bar(self, cd):
        # 实时统计分钟线的情况
        if not self.d_win_flag:
            d_current_appoint_datetime = None
            d_last_appoint_datetime = None
            d_last_extremum_datetime = None
            d_current_extremum_datetime = None

            if self.history.agreement_extremum_d is not None:
                d_last_appoint_datetime = self.history.agreement_extremum_d.appoint_datetime
            if self.history.extremum_d is not None:
                d_last_extremum_datetime = self.history.extremum_d.datetime

            self.history.realtime_analysis_for_cd(cd)
            if self.history.extremum_d is not None:
                d_current_extremum_datetime = self.history.extremum_d.datetime
            
            # D刷新的时候重置h的参数
            if not d_last_extremum_datetime == d_current_extremum_datetime:
                self.d_win_flag = False
                if len(self.start_list) > 0:
                    self.start_list = []
                self.start_list.append(cd)
            else:
                self.start_list.append(cd)
            
            # 开仓时记录开仓后每分钟得数据
            if self.trade_action is not None:
                self.complete_start_list.append(cd)

            if self.history.agreement_extremum_d is not None:
                d_current_appoint_datetime = self.history.agreement_extremum_d.appoint_datetime
            # 如果刷新了协定的D
            if d_last_appoint_datetime is not None and d_current_appoint_datetime is not None and not d_current_appoint_datetime == d_last_appoint_datetime:
                self.opportunity_number = 0
                self.interval_minutes = self.first_interval_minutes 
                self.interval_datetime = None
        elif self.instance_1 is not None:
            # 新程序开仓
            self.instance_1.realtime_analysis_for_cd(cd)

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
        if not self.d_win_flag:
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if tick.current <= self.history.last_cd.low:
                    return True
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
                if tick.current >= self.history.last_cd.high:
                    return True
        elif self.instance_1 is not None: # 实例
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if tick.current <= self.instance_1.last_cd.low:
                    return True
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
                if tick.current >= self.instance_1.last_cd.high:
                    return True
        return False

    """
    开多情况，如果比上一分钟的高点高为真
    开空情况，如果比上一分钟的低点低为真
    """
    def is_exceed_last_cd_low(self, tick):
        if not self.d_win_flag:
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if tick.current >= self.history.last_cd.high:
                    return True
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
                if tick.current <= self.history.last_cd.low:
                    return True
        elif self.instance_1 is not None:
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if tick.current >= self.instance_1.last_cd.high:
                    return True
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT: 
                if tick.current <= self.instance_1.last_cd.low:
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

        return False
    
    """
    重新设置ml为None
    """
    def reset_history_ml(self):
        self.history.ml = None

    """
    是否为赢得状态
    """
    def is_win_point(self, tick):
        if self.trade_action == Cons.ACTION_CLOSE_LONG:
            if (tick.current - self.open_price) > self.unit_value:
                return True
        elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
            if (self.open_price - tick.current) > self.unit_value:
                return True
        return False
    
    """
    获取平常价格
    """
    def get_close_price_by_win_point(self, tick):
        if self.is_win_point(tick):
            return self.close_price
        else:
            return self.close_price_by_lose
    
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
    
    """
    平仓之后的动作
    """
    def after_close(self, tick):
        if not self.d_win_flag:
            if self.open_type == Cons.OPEN_BY_D:
                if self.is_win_point(tick) and (abs(tick.current - self.open_price) > 5 * self.unit_value):
                    self.interval_minutes = self.first_interval_minutes
                    self.opportunity_number = self.opportunity_number_limit
                    self.interval_datetime = None
                    self.d_win_number += 1
                    if self.d_win_number >= self.d_win_number_limit: 
                        self.d_win_flag = True
                        self.init_history1_by_win(self.trade_action)
                else:
                    if self.opportunity_number < self.opportunity_number_limit: # 一共两次机会
                        self.interval_minutes = self.second_interval_minutes
                        # if self.opportunity_number == 2:
                        #     self.interval_minutes = 5
                        self.interval_datetime = str(tick.datetime)
                    else:
                        self.interval_minutes = self.first_interval_minutes
                        self.interval_datetime = None
        else:
            self.after_close_by_instance_1(tick)

        self.reset_price()
        self.trade_action = None
        self.complete_start_list = []
    
    """
    实例1平仓后
    """
    def after_close_by_instance_1(self, tick):
        if self.is_win_point(tick) and (abs(tick.current - self.open_price) > 0 * self.unit_value):
            # self.instance_1_open_number = self.instance_1_open_number_limit
            self.instance_1_open_win_number += 1

    """
    初始化子程序
    """
    def init_history1_by_win(self, trade_action):
        if trade_action == Cons.ACTION_CLOSE_LONG:
            direction = Cons.DIRECTION_UP
        elif trade_action == Cons.ACTION_CLOSE_SHORT:
            direction = Cons.DIRECTION_DOWN
        if direction is not None:    
            if self.instance_1 is None:
                self.instance_1 = FixedMinute(direction, self.complete_start_list)
                # 初始化完成的对应的统计数据
                logging.info(f"init_instance_1 => d:{self.instance_1.extremum_d} => direction => {self.instance_1.breakthrough_direction} => l:{self.instance_1.extremum_l} => last_cd:{self.instance_1.last_cd} same_direction_max_obj => {self.instance_1.same_direction_max_obj} complete_start_list => {self.complete_start_list}")
                logging.info(f"history => d:{self.history.extremum_d} => direction => {self.history.breakthrough_direction} => l:{self.history.extremum_l} => last_cd:{self.history.last_cd}")


    """
    开仓次数增加
    """
    def increase_opportunity_number(self):
        if self.open_type == Cons.OPEN_BY_D:
            self.opportunity_number += 1
        elif self.open_type == Cons.OPEN_BY_H:
            self.h_opportunity_number += 1
        elif self.open_type == Cons.OPEN_BY_L:
            self.l_opportunity_number += 1

    """
    开仓次数增加
    """
    def increase_opportunity_number_by_instance_1(self):
        self.instance_1_open_number += 1
    
    """
    检查是否还有开仓机会
    """
    def has_opportunity(self, open_type):
        if open_type == Cons.OPEN_BY_D:
            if self.opportunity_number < self.opportunity_number_limit:
                return True
        elif open_type == Cons.OPEN_BY_H:
            if self.h_opportunity_number < self.h_opportunity_number_limit:
                return True
        elif open_type == Cons.OPEN_BY_L:
            if self.l_opportunity_number < self.l_opportunity_number_limit:
                return True
        return False
    
    def has_opportunity_by_instance_1(self):
        if self.instance_1_open_number < self.instance_1_open_number_limit:
            return True
        return False
    
    """
    限制赢得次数
    """
    def has_opportunity_by_instance_1_win(self):
        if self.instance_1_open_win_number < self.instance_1_open_win_number_limit:
            return True
        return False
    
    """
    d没有刷新
    """
    def is_same_open_d(self):
        if self.history.extremum_d.datetime == self.last_open_d_datetime:
            return True
        return False
    
    """
    开仓时间
    """
    def after_open_a_position(self):
        self.complete_start_list = deepcopy(self.start_list)