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
from self_strategy.quotation_logic import QuotationLogic
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
    vt_symbol = None # 合约名
    log_obj = None  # 日志对象
    history = None # 行情实例
    instance_1 = None # 右侧策略实例1
    tick_list = []
    close_price_by_lose = None # 止损价位
    close_price = None
    open_price = None # 开仓价格
    open_price_tick = None # 开仓时的tick数据
    agreement_close_price = None
    # 定义参数
    hand_number = 1
    trade_action = None 
    is_new_minute = None # 上一分钟
    last_tick_list = []
    actions = [] # 交易动作
    unit_value = None
    yesterday_close_price = None # 昨日收盘价格 
    yesterday_open_price = None # 昨日开盘价格
    open_type = 1 # 开仓类型
    interval_minutes = 15 # 开仓间隔15分钟
    opportunity_number = 0 # 亏损后允许重开的机会
    opportunity_number_limit = 2000

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

    # --------------------------------------------------------
    allow_open_by_agreement_d = True # 是否回到协定D可以开仓的位置 

    # ------------------------------------------------------- 
    statistic_history = None
    is_close_by_current_ir = False  # 是否可以根据当前的ir进行止盈
    # -------------------------------------------------------
    afer_open_max_ir = None # 开仓后最大的ir

    open_price_agreement_ir = None # 开仓时的ir
    close_by_refresh_agreement_ir = False  # 开仓后再次有效突破时置为True，然后进行平仓，平仓之后回置为False

    # ------------------------------------------------- 1129
    open_price_effective_extremum_d_price = None # 开仓时候的 ed
    open_price_ir_last  = None # 开仓后出现的ir_last
    same_direction_ir = [] # 跟开平仓方向相同的ir

    # 添加参数和变量名到对应的列表
    def __init__(self, 
        vt_symbol,
        unit_value,
        yesterday_open_price,
        yesterday_close_price,
        win_number_limit,
           ):
        """"""
        self.vt_symbol = vt_symbol
        self.unit_value = unit_value
        self.yesterday_open_price = yesterday_open_price
        self.yesterday_close_price = yesterday_close_price
        self.instance_1_open_win_number_limit = win_number_limit

        """
        初始化日志
        """
        self.log_obj = file.get_logger(self.vt_symbol)
        self.history = History(self.yesterday_open_price, self.yesterday_close_price, self.unit_value)
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
            # 统计是否上去
            # self.refresh_allow_open(tick)
            if self.trade_action is None and trade.simulation_can_open_a_position(self.vt_symbol, tick):
                # 出现ml并且当前一分钟没有刷新l
                direction = self.history.breakthrough_direction
                
                if self.history.last_cd is not None:
                     current_ir = QuotationLogic.get_current_ir(direction, self.history.last_cd, minute_cd)
                else:
                    current_ir = None
                if S4Tick.open_a_price_by_effective_lowercase_cr(direction, self.history.effective_lowercase_cr_obj, tick_obj):
                    # 时间间隔起点
                    if self.history.breakthrough_direction == Cons.DIRECTION_UP:
                        # result = self.short(tick.current, self.hand_number)
                        self.add_action(tick, Cons.ACTION_OPEN_SHORT, tick.current - self.unit_value)
                        self.open_price = tick.current - self.unit_value
                        self.open_price_tick = tick
                        # self.open_price_effective_extremum_d_price = self.history.effective_extremum_d_price
                        self.close_price = self.history.effective_lowercase_cr_obj.start_price
                        self.log_obj.info(f"vt_symbol => {self.vt_symbol} \ntrade_type => short_by_d \ndirction => {self.history.breakthrough_direction} \ntick => {tick.current} \neffective_lowercase_cr_obj => {self.history.effective_lowercase_cr_obj} \neffective_lowercase_cr_list => {self.history.effective_lowercase_cr_list} \nlast_cd => {self.history.last_cd}  \ncurrent_ir => {current_ir} \nunit_value => {self.unit_value} \neffective_cr_list => {self.history.effective_cr_list} \neffective_cr_obj => {self.history.effective_cr_obj}")
                        self.trade_action = Cons.ACTION_CLOSE_SHORT
                        self.open_type = Cons.OPEN_BY_D
                        self.increase_opportunity_number()
                        self.after_open_a_position()
                    elif self.history.breakthrough_direction == Cons.DIRECTION_DOWN:
                        # result = self.buy(tick.current, self.hand_number)
                        self.add_action(tick, Cons.ACTION_OPEN_LONG, tick.current + self.unit_value)
                        self.open_price = tick.current + self.unit_value
                        self.open_price_tick = tick
                        # self.open_price_effective_extremum_d_price = self.history.effective_extremum_d_price
                        self.close_price = self.history.effective_lowercase_cr_obj.start_price
                        self.log_obj.info(f"vt_symbol => {self.vt_symbol} \ntrade_type => long_by_d \ndirction => {self.history.breakthrough_direction} \ntick => {tick.current} \neffective_lowercase_cr_obj => {self.history.effective_lowercase_cr_obj} \neffective_lowercase_cr_list => {self.history.effective_lowercase_cr_list} \nlast_cd => {self.history.last_cd}  \ncurrent_ir => {current_ir} \nunit_value => {self.unit_value} \neffective_cr_list => {self.history.effective_cr_list} \neffective_cr_obj => {self.history.effective_cr_obj}")
                        self.trade_action = Cons.ACTION_CLOSE_LONG 
                        self.open_type = Cons.OPEN_BY_D
                        self.increase_opportunity_number()
                        self.after_open_a_position()
                elif False and self.d_win_flag and self.instance_1 is not None  and self.has_opportunity_by_instance_1_win() and self.instance_1.allow_open:
                    direciton1 = self.instance_1.breakthrough_direction
                    # if tick.datetime.day == 2 and tick.datetime.hour == 14 and tick.datetime.minute == 5:
                    #     print(f"ddddddd {tick.datetime} {tick.current} {self.instance_1.extremum_d_price} d => {self.instance_1.extremum_d} =>l {self.instance_1.extremum_l_price} {S4Tick.open_a_position_by_price(direciton1, self.instance_1.extremum_d_price, tick_obj)} direciton1 => {direciton1}")
                    if self.instance_1.extremum_d_price is not None and self.instance_1.extremum_l_price is not None and S4Tick.open_a_position_by_price(direciton1, self.instance_1.extremum_d_price, tick_obj):
                        if direciton1 == Cons.DIRECTION_UP:
                            # result = self.buy(tick.current, self.hand_number)
                            self.add_action(tick, Cons.ACTION_OPEN_LONG, tick.current + self.unit_value)
                            self.open_price = tick.current + self.unit_value
                            self.open_price_tick = tick
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
                            self.open_price_tick = tick
                            logging.info(f"vt_symbol:{self.vt_symbol} => direction:short_by_instance_1 =>  tick1:{tick.current} => l: {self.instance_1.extremum_l} => l_price:{self.instance_1.extremum_l_price} => last_cd1:{self.instance_1.last_cd} => history_dirction1:{direciton1}  d1=> {self.instance_1.extremum_d}  d_price => {self.instance_1.extremum_d_price}")
                            self.trade_action = Cons.ACTION_CLOSE_SHORT
                            self.close_price = self.instance_1.extremum_l_price
                            self.close_price_by_lose = self.instance_1.extremum_l_price
                            self.increase_opportunity_number_by_instance_1()
            elif self.trade_action == Cons.ACTION_CLOSE_LONG:
                current_ir = QuotationLogic.get_current_ir(self.history.breakthrough_direction, self.history.last_cd, minute_cd)
                if S4Tick.close_a_price_by_breakthrough_ir_last(self.trade_action, current_ir, self.open_price_ir_last, self.unit_value):
                    # result = self.sell(tick.current, self.hand_number)
                    self.add_action(tick, Cons.ACTION_CLOSE_LONG, tick.current - self.unit_value)
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction:long \ncurrent_ir => {current_ir} \nopen_price_ir_last => { self.open_price_ir_last}")
                    self.after_close(tick_obj)
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                current_ir = QuotationLogic.get_current_ir(self.history.breakthrough_direction, self.history.last_cd, minute_cd)
                if S4Tick.close_a_price_by_breakthrough_ir_last(self.trade_action, current_ir, self.open_price_ir_last, self.unit_value):
                    # result = self.cover(tick.current, self.hand_number)
                    self.add_action(tick, Cons.ACTION_CLOSE_SHORT, tick.current + self.unit_value)
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction:short \ncurrent_ir => {current_ir} \nopen_price_ir_last => { self.open_price_ir_last}")
                    self.after_close(tick_obj)
                    # logging.info(f"vt_symbol:{self.vt_symbol} => set_close_price_by_agreement => tick_last_price:{tick.current} => close_price => {self.close_price} => agreement_close_price:{self.agreement_close_price} => last_cd:{self.history.last_cd}")
    
    """
    通过该函数收到新的1分钟K线推送。
    """
    def on_bar(self, cd):
        # 实时统计分钟线的情况
        if not self.d_win_flag:
            d_last_extremum_datetime = None
            d_current_extremum_datetime = None

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
 
            # self.refresh_close_by_current_ir(cd)
            # # 通过cr_list 刷新平仓价
            # self.get_close_price_by_cr_list()
            self.append_same_direction_ir()
            self.get_close_price_by_cr_list_and_max_ir()
            self.get_close_price_by_last_second_ir()

            # 检查是否刷新了协定ir
            # self.handle_need_close_by_refresh_agreement_ir()

            # 用分钟级别平仓
            effective_breakthrough_bool = S4Tick.close_a_price_by_effective_breakthrough(self.history.effective_break_through_datetime, cd)
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if S4Tick.close_a_price_by_cd(self.trade_action, self.close_price, cd) or trade.simulation_need_close_position(self.vt_symbol, cd, type='minute') or effective_breakthrough_bool:
                    # result = self.sell(tick.current, self.hand_number)
                    self.add_action(cd, Cons.ACTION_CLOSE_LONG, cd.close - self.unit_value)
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction => long \nclose_price => {self.close_price} \ncd_close => {cd.close} \ncd => {cd} \neffective_breakthrough_bool => {effective_breakthrough_bool}")
                    self.after_close_for_cd(cd)
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                if S4Tick.close_a_price_by_cd(self.trade_action, self.close_price, cd) or trade.simulation_need_close_position(self.vt_symbol, cd, type='minute') or effective_breakthrough_bool:
                    self.add_action(cd, Cons.ACTION_CLOSE_SHORT, cd.close + self.unit_value)
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction => short \nclose_price => {self.close_price} \ncd_close => {cd.close} \ncd => {cd} \neffective_breakthrough_bool => {effective_breakthrough_bool}")
                    self.after_close_for_cd(cd)

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
        open_minute = self.open_price_tick.datetime.minute
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
    获取平仓价通过rc
    """
    def get_close_price_by_win_point_and_cr(self, tick):
        if self.close_by_cr(tick) or self.is_close_by_current_ir:
        # if self.close_by_cr(tick):
            last_cd = self.history.last_cd
            temp_close_price = self.close_price_by_lose
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if tick.current < last_cd.low:
                    temp_close_price = last_cd.low
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                if tick.current > last_cd.high:
                   temp_close_price = last_cd.high
            return temp_close_price
        else:
            return self.close_price_by_lose
    
    """
    通过当前的ir判断是否可以平仓，如果挣钱就使用
    """
    # def close_by_current_ir(self, tick):
    #     if self.is_close_by_current_ir:
    #         if self.is_win_point(tick):
    #             return True
    #         else:
    #             self.is_close_by_current_ir = False
    #     return False
    
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
                    # self.opportunity_number = self.opportunity_number_limit
                    # self.d_win_number += 1
                    # if self.d_win_number >= self.d_win_number_limit:
                    #     if (abs(tick.current - self.open_price) < 30 * self.unit_value): 
                    #         self.d_win_flag = True
                            # self.init_history1_by_win(self.trade_action)
                else:
                    if self.opportunity_number < self.opportunity_number_limit:
                        self.interval_minutes = self.second_interval_minutes
                    else:
                        self.interval_minutes = self.first_interval_minutes
        else:
            self.after_close_by_instance_1(tick)

        self.reset_price()
        self.trade_action = None
        self.complete_start_list = []
        self.is_close_by_current_ir = False
        self.close_by_refresh_agreement_ir = False # 平仓后设置为False
        self.same_direction_ir = []

    """
    使用分钟级别去平仓
    """
    def after_close_for_cd(self, cd):
        self.reset_price()
        self.trade_action = None
        self.complete_start_list = []
        self.is_close_by_current_ir = False
        self.close_by_refresh_agreement_ir = False # 平仓后设置为False
        self.same_direction_ir = []
    
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
    开仓后触发的处理
    将需要回到D设置为False
    将协定cr的tag设置为False,必须重新刷新协定cr才允许开仓
    """
    def after_open_a_position(self):
        self.allow_open_by_agreement_d = False
        self.history.effective_lowercase_cr_obj.tag = False
 
    """
    刷新是否可以开仓
    """
    def refresh_allow_open(self, tick):
        if (not self.d_win_flag) and not self.allow_open_by_agreement_d and self.trade_action is None and self.history.agreement_cr_obj is not None: 
            if self.history.breakthrough_direction == Cons.DIRECTION_UP:
                if tick.current > self.history.agreement_cr_list[-1].low:
                    self.allow_open_by_agreement_d = True
            elif self.history.breakthrough_direction == Cons.DIRECTION_DOWN:
                if tick.current < self.history.agreement_cr_list[-1].high:
                    self.allow_open_by_agreement_d = True
    
    """
    通过rc的方式平仓
    当前的cr长度需要大于30个单位，并且是赢的
    """
    def close_by_cr(self, tick):
        if self.history.cr_obj.length > 40 * self.unit_value:
            last_cd = self.history.cr_list[-1]
            if self.trade_action == Cons.ACTION_CLOSE_LONG and self.history.cr_obj.direction == Cons.DIRECTION_UP:
                if tick.current < last_cd.low:
                    return True
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT and self.history.cr_obj.direction == Cons.DIRECTION_DOWN:
                if tick.current > last_cd.high:
                    return True
        return False
    
    """
    通过cr_list获取平仓价
    """
    def get_close_price_by_cr_list(self):
        if self.trade_action is not None and self.history.cr_obj is not None:
            if self.history.cr_obj.length > 30 * self.unit_value:
                first_cd = self.history.cr_list[0]
                first_cd_ptime = Logic.ptime(first_cd.datetime)
                if first_cd_ptime > self.open_price_tick.datetime:
                    if self.trade_action == Cons.ACTION_CLOSE_LONG and self.history.cr_obj.direction == Cons.DIRECTION_UP:
                        self.close_price = max(self.close_price, first_cd.low)
                        logging.info(f"refresh close price by cr_list => trade_action => {self.trade_action} => old_close_price:{self.close_price}  current_close_price =>{self.close_price} => first_cd => {first_cd} cr_list => {self.history.cr_list} open_price_tick.datetime => {self.open_price_tick.datetime}")
                    elif self.trade_action == Cons.ACTION_CLOSE_SHORT and self.history.cr_obj.direction == Cons.DIRECTION_DOWN:
                        self.close_price = min(self.close_price, first_cd.high)
                        logging.info(f"refresh close price by cr_list => trade_action => {self.trade_action} => old_close_price:{self.close_price}  current_close_price =>{self.close_price} => first_cd => {first_cd} cr_list => {self.history.cr_list} open_price_tick.datetime => {self.open_price_tick.datetime}")

    """
    通过cr_list和ir获取平仓价
    """
    def get_close_price_by_cr_list_and_max_ir(self):
        if self.trade_action is not None and self.history.cr_obj is not None:
            if self.history.cr_obj.length > 50 * self.unit_value and self.history.max_ir_by_cr.length > 10 * self.unit_value:
                first_cd = self.history.cr_list[0]
                last_cd = self.history.cr_list[-1]
                first_cd_ptime = Logic.ptime(first_cd.datetime)
                if first_cd_ptime > self.open_price_tick.datetime:
                    if self.trade_action == Cons.ACTION_CLOSE_LONG and self.history.cr_obj.direction == Cons.DIRECTION_UP:
                        self.close_price = max(self.close_price, last_cd.low)
                        self.log_obj.info(f"get_close_price_by_cr_list_and_max_ir \ntrade_action => {self.trade_action} \nold_close_price => {self.close_price} \ncurrent_close_price => {self.close_price} \nfirst_cd => {first_cd} \nlast_cd => {last_cd} \ncr_list => {self.history.cr_list} \ncr_obj => {self.history.cr_obj} \nopen_price_tick.datetime => {self.open_price_tick.datetime}  \nmax_ir_by_cr => {self.history.max_ir_by_cr}")
                    elif self.trade_action == Cons.ACTION_CLOSE_SHORT and self.history.cr_obj.direction == Cons.DIRECTION_DOWN:
                        self.close_price = min(self.close_price, last_cd.high)
                        self.log_obj.info(f"refresh_close_price_by_cr_list_and_max_ir \ntrade_action => {self.trade_action} \nold_close_price => {self.close_price} \ncurrent_close_price => {self.close_price}  \nfirst_cd => {first_cd} \nlast_cd => {last_cd} \ncr_list => {self.history.cr_list} \ncr_obj => {self.history.cr_obj} \nopen_price_tick.datetime => {self.open_price_tick.datetime}  \nmax_ir_by_cr => {self.history.max_ir_by_cr}")
    
    """
    通过开仓后最大的max_ir刷新开仓价格
    如果是平多，则max_ir方向向上
    如果是平多，则max_ir方向向下
    """
    def get_close_price_by_max_ir(self):
        if self.trade_action is not None and self.history.current_ir is not None:
            unit_value_limit = 10 * self.unit_value
            ir_ptime = Logic.ptime(self.history.current_ir.datetime)
            if ir_ptime > self.open_price_tick.datetime:
                if self.trade_action == Cons.ACTION_CLOSE_LONG and self.history.current_ir.direction == Cons.DIRECTION_UP:  
                    if self.afer_open_max_ir is None or (self.history.current_ir.length > self.afer_open_max_ir.length and self.history.current_ir.length > unit_value_limit):
                        self.afer_open_max_ir = deepcopy(self.history.current_ir)
                        old_close_price = self.close_price
                        self.close_price = max(self.close_price, self.afer_open_max_ir.start_price -1*self.unit_value)
                        self.log_obj.info(f"get_close_price_by_max_ir => close_long \n trade_action => {self.trade_action} \n old_close_price => {old_close_price} \n current_close_price => {self.close_price} \n afer_open_max_ir => {self.afer_open_max_ir} \n open_price_tick.datetime => {self.open_price_tick.datetime}")
                elif self.trade_action == Cons.ACTION_CLOSE_SHORT and self.history.current_ir.direction == Cons.DIRECTION_DOWN:
                    if self.afer_open_max_ir is None or (self.history.current_ir.length > self.afer_open_max_ir.length and self.history.current_ir.length > unit_value_limit):
                        self.afer_open_max_ir = deepcopy(self.history.current_ir)
                        old_close_price = self.close_price
                        self.close_price = min(self.close_price, self.afer_open_max_ir.start_price + 1*self.unit_value)
                        self.log_obj.info(f"get_close_price_by_max_ir => close_short \n trade_action => {self.trade_action} \n old_close_price => {old_close_price} \n current_close_price => {self.close_price} \n afer_open_max_ir => {self.afer_open_max_ir} \n open_price_tick.datetime => {self.open_price_tick.datetime}")

    """
    通过开仓后最近的current_ir且current_ir的长度大于10单位
    如果是平多，则current_ir方向向上
    如果是平多，则current_ir方向向下
    """
    def get_close_price_by_current_ir(self):
        if self.trade_action is not None and self.history.current_ir is not None:
            unit_value_limit = 10 * self.unit_value
            ir_ptime = Logic.ptime(self.history.current_ir.datetime)
            if ir_ptime > self.open_price_tick.datetime:
                if self.trade_action == Cons.ACTION_CLOSE_LONG and self.history.current_ir.direction == Cons.DIRECTION_UP:  
                    if self.history.current_ir.length > unit_value_limit:
                        old_close_price = self.close_price
                        # current_price = self.history.current_ir.start_price -1*self.unit_value
                        current_price = self.history.current_ir.start_price
                        if self.close_price is None:
                            self.close_price = current_price
                        else:
                            self.close_price = max(self.close_price, current_price)
                        self.open_price_ir_last = deepcopy(self.history.current_ir)
                        self.log_obj.info(f"get_close_price_by_current_ir => close_long \n trade_action => {self.trade_action} \n old_close_price => {old_close_price} \n current_close_price => {self.close_price} \n current_ir => {self.history.current_ir} \n open_price_tick.datetime => {self.open_price_tick.datetime}")
                elif self.trade_action == Cons.ACTION_CLOSE_SHORT and self.history.current_ir.direction == Cons.DIRECTION_DOWN:
                    if self.history.current_ir.length > unit_value_limit:
                        old_close_price = self.close_price
                        # current_price = self.history.current_ir.start_price + 1*self.unit_value
                        current_price = self.history.current_ir.start_price
                        if self.close_price is None:
                            self.close_price = current_price
                        else:
                            self.close_price = min(self.close_price, current_price)
                        self.open_price_ir_last = deepcopy(self.history.current_ir)
                        self.log_obj.info(f"get_close_price_by_current_ir => close_short \n trade_action => {self.trade_action} \n old_close_price => {old_close_price} \n current_close_price => {self.close_price} \n current_ir => {self.history.current_ir} \n open_price_tick.datetime => {self.open_price_tick.datetime}")

        """
    通过开仓后最近的current_ir且current_ir的长度大于10单位
    如果是平多，则current_ir方向向上
    如果是平多，则current_ir方向向下
    """
    def get_close_price_by_last_second_ir(self):
        if self.trade_action is not None and len(self.same_direction_ir) > 1:
            last_second_ir = self.same_direction_ir[-2]
            current_price = last_second_ir.start_price
            ir_ptime = Logic.ptime(last_second_ir.datetime)
            if ir_ptime > self.open_price_tick.datetime and not current_price == self.close_price:
                if self.trade_action == Cons.ACTION_CLOSE_LONG and last_second_ir.direction == Cons.DIRECTION_UP:  
                    old_close_price = self.close_price
                    # current_price = last_second_ir.start_price -1*self.unit_value
                    if self.close_price is None:
                        self.close_price = current_price
                    else:
                        self.close_price = max(self.close_price, current_price) 
                    self.log_obj.info(f"get_close_price_by_last_second_ir => close_long \n trade_action => {self.trade_action} \n old_close_price => {old_close_price} \n current_close_price => {self.close_price} \n last_second_ir => {last_second_ir} \n open_price_tick.datetime => {self.open_price_tick.datetime} \nsame_direction_ir => {self.same_direction_ir}")
                elif self.trade_action == Cons.ACTION_CLOSE_SHORT and last_second_ir.direction == Cons.DIRECTION_DOWN:
                    old_close_price = self.close_price
                    # current_price = last_second_ir.start_price + 1*self.unit_value
                    if self.close_price is None:
                        self.close_price = current_price
                    else:
                        self.close_price = min(self.close_price, current_price)
                    self.log_obj.info(f"get_close_price_by_last_second_ir => close_short \n trade_action => {self.trade_action} \n old_close_price => {old_close_price} \n current_close_price => {self.close_price} \n last_second_ir => {last_second_ir} \n open_price_tick.datetime => {self.open_price_tick.datetime} \nsame_direction_ir => {self.same_direction_ir}")



    """
    是否回到cr的起点
    """   
    def is_allow_open(self):
        return self.history.allow_open

    """
    是否满足rc刷新次数限制
    """
    def has_change_direction_number(self):
        return self.history.change_direction_number >= 1

    """
    看是否出现可以平仓的ir
    """
    def refresh_close_by_current_ir(self, cd):
       if self.trade_action is not None and not self.is_close_by_current_ir:
        if self.history.current_ir is not None:
            temp_ptime = Logic.ptime(cd.datetime)
            if temp_ptime > self.open_price_tick.datetime:
                if self.trade_action == Cons.ACTION_CLOSE_LONG:
                    if self.history.current_ir.direction == Cons.DIRECTION_UP and self.history.current_ir.length > 10 * self.unit_value:
                        self.is_close_by_current_ir = True
                        self.close_price = max(self.close_price, self.history.current_ir.start_price)
                        logging.info(f"refresh close price by ir \n trade_action => {self.trade_action}  \n old_close_price => {self.close_price} \n start_price => {self.history.current_ir.start_price} \n current_ir:{self.history.current_ir} cd \n {cd} open_price_tick.datetime => {self.open_price_tick.datetime}")
                elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                    if self.history.current_ir.direction == Cons.DIRECTION_DOWN and self.history.current_ir.length > 10 * self.unit_value:
                        self.is_close_by_current_ir = True
                        self.close_price = min(self.close_price, self.history.current_ir.start_price)
                        logging.info(f"refresh close price by ir \n trade_action => {self.trade_action}  \n old_close_price => {self.close_price} \n start_price => {self.history.current_ir.start_price} \n current_ir:{self.history.current_ir} cd \n {cd} open_price_tick.datetime => {self.open_price_tick.datetime}")


    """
    开仓状态下，如果再次有效突破，就平仓
    """
    def handle_need_close_by_refresh_agreement_ir(self):
        if self.trade_action is not None and self.history.agreement_ir is not None:
            if self.history.agreement_ir.direction == self.open_price_agreement_ir.direction and not self.history.agreement_ir.datetime == self.open_price_agreement_ir.datetime:
                self.close_by_refresh_agreement_ir = True
                self.log_obj.info(f"handle_need_close_by_refresh_agreement_ir \n agreement_ir => {self.history.agreement_ir} \nopen_price_agreement_ir => {self.open_price_agreement_ir}")
    
    
    """
    统计跟开仓方向一致的ir
    """
    def append_same_direction_ir(self):
        if self.trade_action == Cons.ACTION_CLOSE_LONG:
            if self.history.current_ir.direction == Cons.DIRECTION_UP and self.history.current_ir.length > 10 * self.unit_value:
                self.same_direction_ir.append(self.history.current_ir)
                self.open_price_ir_last = deepcopy(self.history.current_ir)
        elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
            if self.history.current_ir.direction == Cons.DIRECTION_DOWN and self.history.current_ir.length > 10 * self.unit_value:
                self.same_direction_ir.append(self.history.current_ir)
                self.open_price_ir_last = deepcopy(self.history.current_ir)