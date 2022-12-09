"""
main.py
读取data文件夹中的所有csv文件，针对每个文件计算出该交易策略的胜率和赚钱点数
"""
from copy import deepcopy
from self_strategy.constants import Constants
from self_strategy.logic import Logic
from self_strategy.quotation_logic import QuotationLogic
from types import SimpleNamespace
import sys

from datetime import datetime
# 
class Minute:
    breakthrough_direction = None # 突破的方向 -1 开空 1开多
    max_l_to_d_interval = None  # 最大上涨的间隔,即R
    current_max_l_to_d_interval = None # 当前的上涨间隔
    max_r = None  # 表示从dn-ln的最大值，d1点开始
    current_max_r = None # 表示从dn-ln的当前值
    rrn = None  # 逆趋势止盈使用的参数  todo 暂时不使用

    current_status = Constants.STATUS_NONE  # 当前状态，目前就无状态跟非加速振荡

    actions = []  # 记录所有的动作，包括开空，开多，逆开空，逆开多，注意：逆趋势下是两倍仓位
    extremum_d_price = None  # 极致d的price
    extremum_d = None  # 极值点D
    effective_extremum_d_price = None # 有效D的价格
    effective_extremum_d = None # 有效D

    agreement_extremum_d = None # todo 协议D,标定开仓信号 暂时不用了
    # effective_extremum_d = None # 有效D 
    extremum_l_price = None # 极值点l的price
    extremum_l = None # 极值点l
    agreement_extremum_l = None # 协定L 暂时不用了

    h_price = None # h点，表示比仅次于d点第二高点
    h_cd = None
    agreement_h_cd = None # 协定h

    history_status = Constants.HISTORY_STATUS_OF_NONE # 历史状态
    last_cd = None # 上一点
    max_amplitude = None # 最大幅度对象
    last_max_amplitude = None # 上一个Rmax
    change_direction_number = 0 # rc改变方向的次数
    h_price_max = None # h的极值
    trade_action = None
    # ml = None # 出现小级别逆趋势后的低点，需比L的值大
    # ml_1_price  = None # 用于止盈
    m_max_r = None  # 小级别r
    M_MAX_R = None  # 小级别R
    unit_value = 0 # 单位值
    # max_limit = 1 # 最大开仓次数限制 todo 暂时无使用
    has_open_a_position_times = 0 # 已开仓次数
    l_start_cd = None # l开仓起点
    h_start_cd = None # h开仓起点
    d_start_cd = None # d开仓起点
    interval_minutes = 10
    refresh_d_minute_count = 0 # 协定D刷新的间隔分钟数

    #---------------------
    d_minute_count_limit = 5 # 协定D刷新的间隔分钟数

    refresh_h_minute_count = 0 # 协定H刷新的间隔分钟数
    h_minute_count_limit = 5 # 协定H最小间隔限制

    yesterday_open_price = None # 昨日开盘价格
    yesterday_close_price = None # 昨日收盘价格
    # yesterday_direction = None # 上一个交易日的方向  以昨日开仓跟收盘价定方向

    start_cd = None # 当日的起点

    #-----------------------------------
    last_max_price = None # 前一个交易日的最大价格
    last_min_price = None # 前一个交易日的最小价格
    cr_list = [] # 连续趋势的统计
    cr_obj = None # 连续趋势的幅度 默认为0
    temp_cr_list = [] # 当前分钟的方向跟主cr_Obj不一致时
    temp_cr_obj = None 

    agreement_cr_list = [] # 协定cr_list
    agreement_cr_obj = None # 协定cr_obj

    max_cr_list = [] # 最大的连续趋势区间
    max_cr_obj = None # 最大的区间幅度
    fictitious_cd = None

    #-------------------------------------1116
    allow_open = True # 允许开仓
    max_ir_by_cr = None # 从cr_list中统计出最大的ir
    max_lowercase_ir_by_cr = None # 从cr_list中获取最大的小ir
    current_ir = None # 当前的ir
    ir_last = None # 用于判断有效突破的[同方向]
    effective_ir_last = None # 有效ir_last

    agreement_ir = None # 协定ir

    #---------------------------------------1128
    effective_cr_list = [] # 有效cr_list
    effective_cr_obj = None # 有效cr_obj

    effective_break_through_datetime = None # 有效突破时间

    #-----------------------------------------1202
    effective_lowercase_cr_list = []
    effective_lowercase_cr_obj = None 

    """
    初始化
    """

    def __init__(self, yesterday_open_price, yesterday_close_price, unit_value):
        # 昨日收盘价格
        self.yesterday_open_price = yesterday_open_price
        # 昨日收盘价
        self.yesterday_close_price = yesterday_close_price
        self.unit_value = unit_value
        # 所有的list跟dict需要重置
        self.max_l_to_d_interval = None
        self.max_r = None
        self.actions = []
        self.cr_list = []
        self.max_cr_list = []
        self.max_amplitude = None
        self.last_max_amplitude = None
        self.m_max_r = None  # 小级别r
        self.M_MAX_R = None  # 小级别R
        self.max_ir_by_cr = None # cr_list区间中最大的ir
        self.current_ir = None # 当前的ir
        # self.agreement_cr_list = [] # 协定cr的列表
        # self.agreement_cr_obj = None # 协定cr对象
        self.effective_cr_list = [] # 有效cr_list
        self.effective_cr_obj = None # 有效cr_obj
        self.temp_cr_list = [] # 当前分钟的方向跟主cr_Obj不一致时
        self.temp_cr_obj = None  # 
        
        self.reset_effective_lowercase_cr()

    """
    添加对应的动作，目前包括开空、平空、开多、平多
    """

    def add_action(self, cd, action, price, actions_index=Constants.ACTIONS_INDEX_DEFAULT):
        record = {
            "price": price,
            "action": action,
            "datetime": cd.datetime
        }

        if actions_index == Constants.ACTIONS_INDEX_DEFAULT:
            self.actions.append(record)
        return record


    """
    重置状态
    """
    def reset_status(self):
        self.current_status = Constants.STATUS_NONE

    """
    将当前状态设置成某状态
    """
    def set_status(self, status):
        self.current_status = status

    """
    设置最大的l_to_d间隔数据
    """
    def set_max_l_to_d_interval_obj(self, obj):
        if (self.max_l_to_d_interval is None) or (obj.length > self.max_l_to_d_interval.length):
            self.max_l_to_d_interval = obj

    """
    设置开仓的点位
    """
    def set_l_start_cd(self, cd):
       if self.l_start_cd is None:
            if self.is_same_direction(self.extremum_l) or (self.extremum_l.open == self.extremum_l.close):
                self.l_start_cd = self.extremum_l
                self.l_start_cd.price = self.extremum_l.open
            elif self.is_same_direction(cd) and self.can_set_start_cd(cd):
                self.l_start_cd = cd
                if self.breakthrough_direction == Constants.DIRECTION_UP:
                    self.l_start_cd.price = cd.low
                elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                    self.l_start_cd.price = cd.high

    """
    设置D的开始点
    """
    def set_d_start_cd(self, cd):
        if self.d_start_cd is None:
            if not self.is_same_direction(self.extremum_d) or (self.extremum_d.open == self.extremum_d.close):
                self.d_start_cd = self.extremum_d
                self.d_start_cd.price = self.extremum_d.open
            elif not self.is_same_direction(cd) and self.can_set_start_cd_by_d(cd):
                self.d_start_cd = cd
                if self.breakthrough_direction == Constants.DIRECTION_UP:
                    self.d_start_cd.price = cd.high
                elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                    self.d_start_cd.price = cd.low
        
    """
    设置开仓的点位
    """
    def set_h_start_cd(self, cd):
       if self.h_start_cd is None:
            if not self.is_same_direction(self.h_cd) or (self.h_cd.open == self.h_cd.close):
                self.h_start_cd = self.h_cd
                self.h_start_cd.price = self.h_cd.open
            elif not self.is_same_direction(cd) and self.can_set_start_cd_by_h(cd):
                self.h_start_cd = cd
                if self.breakthrough_direction == Constants.DIRECTION_UP:
                    self.h_start_cd.price = cd.high
                elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                    self.h_start_cd.price = cd.low

    """
    判断是否可以设置为L的起点
    """
    def can_set_start_cd(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.low >= self.extremum_l_price:
                return True
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            if cd.high <= self.extremum_l_price:
                return True
        return False
    
    """
    判断是否可以设置H的起点
    """
    def can_set_start_cd_by_h(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.high <= self.h_price:
                return True
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            if cd.low >= self.h_price:
                return True
        return False
    
    """
    判断是否可以设置D的起点
    """
    def can_set_start_cd_by_d(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.high <= self.extremum_d_price:
                return True
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            if cd.low >= self.extremum_d_price:
                return True
        return False
    
    
    """
    rrn 表示的是寻找Dn过程中，出现比Dn小的Hn过程的最大值
    """
    def set_rrn(self, current_rrn):
       if self.rrn is None or current_rrn > self.rrn:
        self.rrn = current_rrn 

    """
    设置d1极值
    """
    def set_extremum_d(self, dn):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if (self.extremum_d_price is None) or dn.high >= self.extremum_d_price:
                self.extremum_d_price = dn.high
                self.extremum_d = dn
                self.after_set_extremum_d()
        else:
            if (self.extremum_d_price is None) or dn.low <= self.extremum_d_price:
                self.extremum_d_price = dn.low
                self.extremum_d = dn
                self.after_set_extremum_d()
    
    """
    新的D跟上一个D间隔超过30时,产生协定D
    """
    def before_set_extremum_d(self, dn):
        if self.extremum_d is not None and self.refresh_d_minute_count > self.d_minute_count_limit:
            self.agreement_extremum_d = deepcopy(self.extremum_d)
            self.agreement_extremum_d.price = self.extremum_d_price
            self.agreement_extremum_d.appoint_datetime = dn.datetime
            self.agreement_extremum_d.tag = False

    """
    D刷新后重置L
    """
    def after_set_extremum_d(self):
        self.refresh_d_minute_count = 0
        self.d_start_cd = None
        # 重置l数据
        self.reset_extremum_l()

    
    """
    重新设置极值d
    """
    def reset_extremum_d(self):
        self.extremum_d = None
        self.extremum_d_price = None
        self.d_start_cd = None
        self.agreement_extremum_d = None
        self.refresh_d_minute_count = 0
        # 重置L
        self.reset_extremum_l()
        # 重置有效D
        self.reset_effective_extremum_d()

    """
    设置l的相关值
    """
    def set_extremum_l(self, ln):
        if self.extremum_d_price is not None:
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if (self.extremum_l_price is None) or ln.low < self.extremum_l_price:
                    self.before_set_extremum_l()
                    self.extremum_l_price = ln.low
                    self.extremum_l = ln
                    self.after_set_extremum_l()
                else:
                    # 如果是L状态，就设置为逆趋势状态
                    if self.extremum_l_price is not None:
                        self.set_h_price(ln)
            else:
                if (self.extremum_l_price is None) or ln.high > self.extremum_l_price:
                    self.before_set_extremum_l()
                    self.extremum_l_price = ln.high
                    self.extremum_l = ln
                    self.after_set_extremum_l()
                else:
                    if self.extremum_l_price is not None:
                        self.set_h_price(ln)
    
    """
    在设置新的L之前刷新协定L
    """
    def before_set_extremum_l(self):
        if self.extremum_l is not None:
            self.agreement_extremum_l = deepcopy(self.extremum_l)
            self.agreement_extremum_l.price = self.extremum_l_price

    """
    设置极值L后的动作，设置状态为L
    将策略三相关的参数设置为None
    """
    def after_set_extremum_l(self):
        # 设置L为最新的状态
        self.l_start_cd = None
        self.reset_h_price()
        # 出现新的l刷新开仓次数
        # self.has_open_a_position_times = 0


    """
    重置extremum_l的值
    """
    def reset_extremum_l(self):
        self.extremum_l = None
        self.extremum_l_price = None
        self.l_start_cd = None
        # 重置开盘次数
        self.has_open_a_position_times = 0
        # 重置h
        self.reset_h_price()
        # 重置h_price_max
        self.h_price_max = None
        self.agreement_extremum_l = None
    
    """
    设置h_price参数
    """
    def set_h_price(self, cd):
        if self.extremum_d_price is not None and Logic.is_high_point(self.breakthrough_direction, self.last_cd, cd):
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if (self.h_price is None and cd.high > self.extremum_l.high) or (self.h_price is not None and cd.high > self.h_price):
                        self.before_set_h_price(cd)
                        self.h_price = cd.high
                        self.h_cd = cd
                        self.after_set_h_price()
                        if (self.h_price_max is None) or self.h_price > self.h_price_max:
                            self.h_price_max = self.h_price
            elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                if (self.h_price is None and cd.low < self.extremum_l.low) or (self.h_price is not None and cd.low < self.h_price):
                    self.before_set_h_price(cd)
                    self.h_price = cd.low
                    self.h_cd = cd
                    self.after_set_h_price()
                    if (self.h_price_max is None) or self.h_price < self.h_price_max:
                        self.h_price_max = self.h_price
    
    """
    h_price设置之前的处理逻辑
    """
    def before_set_h_price(self, cd):
        # h点刷新，重置开始点
        if self.h_cd is not None and self.refresh_h_minute_count > self.h_minute_count_limit:
            self.agreement_h_cd = deepcopy(self.h_cd)
            self.agreement_h_cd.price = self.h_price
            self.agreement_h_cd.appoint_datetime = cd.datetime


    """
    h_price设置之后的处理逻辑
    """
    def after_set_h_price(self):
        # h点刷新，重置开始点
       self.h_start_cd = None
       self.refresh_h_minute_count = 0


    """
    重新设置ml_1_price为None
    """
    # def reset_ml_1_price(self):
    #     self.ml_1_price = None

    """
    设置开仓状态
    """ 
    def set_open_trade_action(self):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            self.trade_action = Constants.ACTION_OPEN_LONG
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            self.trade_action = Constants.ACTION_OPEN_SHORT

    """
    出现ml1
    """
    # def find_open_a_price(self, cd):
    #     if self.ml is not None:
    #         if self.breakthrough_direction == Constants.DIRECTION_UP:
    #             if cd.high > self.last_cd.high:
    #                 return True
    #         elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
    #             if cd.low < self.last_cd.low:
    #                 return True
    #     return False

    """
    如果当前的R比M_MAX_R 还大就结束统计，重新开始统计逆趋势
    """ 
    def restart_by_M_MAX_R(self):
        if self.M_MAX_R is None or self.current_max_l_to_d_interval is None:
            return False
        if self.M_MAX_R.length < self.current_max_l_to_d_interval.length:
            return True
        return False

    """
    重置h_price参数
    """     
    def reset_h_price(self):
        self.h_price = None
        self.h_cd = None
        self.h_start_cd = None
        self.agreement_h_cd = None
        self.refresh_h_minute_count = 0

    """
    当前状态为STATUS_NONE时的逻辑
    """

    def histoty_status_none(self, cd):
        # 初始化时为十字星不处理
        if Logic.is_crossing_starlike(cd):
            if self.breakthrough_direction is None:
                return
            else:
                cd.direction = self.breakthrough_direction

        # 设置走势方向，设置最大的幅度对象，包括最大幅度的起始、结束值跟幅度
        self.init_set_max_amplitude(cd)
        # 设置最大的上涨幅度
        self.max_l_to_d_interval = None
        # self.init_max_l_to_d_interval_obj(cd)
        # 初始化最大的下降幅度
        self.max_r = None
        # 设置d
        self.set_extremum_d(cd)
        # 设置rrn
        self.rrn = None

        self.history_status = Constants.HISTORY_STATUS_OF_TREND
    
    """
    初始化设置max_l_to_d_interval
    """
    def init_max_l_to_d_interval_obj(self, cd):
        self.max_l_to_d_interval = None
        if cd.direction == Constants.DIRECTION_UP:
            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.low, cd.high)
        else:
            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.high, cd.low)
        self.max_l_to_d_interval = max_l_to_d_obj

    """
    初始化设置max_r
    """
    def init_max_r_obj(self, cd):
        self.max_r = None
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            len = abs(cd.open - cd.low)
            end_len = abs(cd.high - cd.close)

            if len > end_len:
                max_r_obj = QuotationLogic.amplitude_obj(cd.open, cd.low)
            else:
                max_r_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
        else:
            len = abs(cd.high - cd.open)
            end_len = abs(cd.close - cd.low)

            if len > end_len:
                max_r_obj = QuotationLogic.amplitude_obj(cd.open, cd.high)
            else:
                max_r_obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
        self.max_r = max_r_obj

    
    """
    分析统计R、r、rrn
    """
    def statistic(self, cd):
        # 统计R、统计rrn
        self.history_statistic_max_l_to_d(cd)

        # 统计r
        self.history_statistic_max_r(cd)

        # 处理ir
        self.handle_current_ir(cd)

        # 处理max_ir_by_cr
        self.handle_max_ir_by_cr()

        # 处理方向的逻辑
        self.handle_direction(cd)

        # 有效趋势
        self.handle_effective_trend()

        # 标定有效极致D
        self.handle_effective_extremum_d(cd)
        
        # 设置有效小cr[有效反弹]
        self.handle_effective_lowercase_cr(cd)
        
        # 有效突破跟非有效突破
        self.handle_breakthrough(cd)
        
        # 处理有效无序
        self.handle_effective_disorder(cd)
    
    """
    当CR大于50单位，且其中IR大于10单位设置为有效趋势
    """
    def handle_effective_trend(self):
        if self.cr_obj is not None and self.max_ir_by_cr is not None and self.current_ir is not None:
            if self.breakthrough_direction == self.cr_obj.direction:
                if self.cr_obj.length > 80 * self.unit_value and  (self.max_ir_by_cr.length > 10 * self.unit_value):
                        self.effective_cr_list = deepcopy(self.cr_list)
                        self.effective_cr_obj = deepcopy(self.cr_obj) 
                        self.set_ir_last(effective=True)
                        # 如果有效D存在就重置
                        if self.effective_extremum_d_price is not None:
                            self.reset_effective_extremum_d()    
                        if self.effective_lowercase_cr_obj is not None:
                            self.reset_effective_lowercase_cr()
                        # print(f"有效趋势 => effective_cr_obj => {self.effective_cr_obj} \ncr_list => {self.effective_cr_list} \nextremum_d => {self.extremum_d} \n")
                else:
                    # print(f"无有效趋势 => cr_obj => {self.cr_obj}")
                    self.set_ir_last()
    
    """
    重置有效cr
    """
    def reset_effective_cr(self):
            self.effective_cr_list = []
            self.effective_cr_obj = None 
            # 重置ed
            self.reset_effective_extremum_d()
            # 重置e_ir_last
            self.effective_ir_last = None
            # 重置有效小cr
            self.reset_effective_lowercase_cr()
    
    """
    有效趋势后寻找有效小cr
    """
    def handle_effective_lowercase_cr(self, cd):
        # 有效趋势->有效d->有效反弹
        if self.effective_cr_obj is not None and self.effective_ir_last is not None and self.effective_extremum_d is not None:
            # 小cr_obj不存在
            if self.effective_lowercase_cr_obj is None:
                if self.cr_obj is not None and (not self.cr_obj.direction == self.effective_cr_obj.direction):
                    if self.is_effective_rebound(): 
                        # print(f"这里开始设置 => cr_obj => {self.cr_obj} max_ir_by_cr => {self.max_ir_by_cr} effective_ir_last => {self.effective_ir_last} cr_list => {self.effective_cr_list}")
                        self.effective_lowercase_cr_list = deepcopy(self.cr_list)
                        self.effective_lowercase_cr_obj = deepcopy(self.cr_obj)
                        self.effective_lowercase_cr_obj.finish = False
            else:
                if not self.effective_lowercase_cr_obj.finish:
                    if self.cr_obj is not None:
                        if self.effective_lowercase_cr_obj.direction == self.cr_obj.direction:
                            self.effective_lowercase_cr_list = deepcopy(self.cr_list)
                            self.effective_lowercase_cr_obj = deepcopy(self.cr_obj)
                            self.effective_lowercase_cr_obj.finish = False
                        else:
                            self.effective_lowercase_cr_obj.finish = True
                            self.effective_lowercase_cr_obj.tag = True
                            # print(f"完成设置有效 lowercase_cr_obj => {self.effective_lowercase_cr_obj} \neffective_lowercase_cr_list =>{self.effective_lowercase_cr_list} \nmax_ir_by_cr => {self.max_ir_by_cr} \neffective_cr_obj => {self.effective_cr_obj} \ncr_list => {self.cr_list} \n cr_obj => {self.cr_obj}")
                if self.effective_lowercase_cr_obj.finish:
                    if self.effective_lowercase_cr_obj.direction == Constants.DIRECTION_UP:
                        if cd.low < self.effective_lowercase_cr_obj.start_price:
                            self.reset_effective_lowercase_cr()
                            # print(f"重置有效小cr")
                    elif self.effective_lowercase_cr_obj.direction == Constants.DIRECTION_DOWN:
                        if cd.high > self.effective_lowercase_cr_obj.start_price:
                            self.reset_effective_lowercase_cr()
                            # print(f"重置有效小cr")
    
    """
    是否有效反弹
    """
    def is_effective_rebound(self):
        if self.effective_ir_last.direction == Constants.DIRECTION_UP:
            if self.cr_obj.end_price < self.effective_ir_last.start_price:
                return True 
        elif self.effective_ir_last.direction == Constants.DIRECTION_DOWN:
            if self.cr_obj.end_price > self.effective_ir_last.start_price:
                return True
        return False
        
    
    """
    重置有效小cr
    """
    def reset_effective_lowercase_cr(self):
        self.effective_lowercase_cr_list =[]
        self.effective_lowercase_cr_obj = None

        
    """
    设置有效D,初始bk_type=-1
    """
    def handle_effective_extremum_d(self, cd):
        if self.effective_cr_obj is not None and self.effective_cr_obj.direction == self.breakthrough_direction:
            if not self.exceed_extremum_d(cd):
                first_cd = self.effective_cr_list[0]
                first_cd_ptime = Logic.ptime(first_cd.datetime)
                extremum_d_ptime = Logic.ptime(self.extremum_d.datetime)
                if self.effective_extremum_d is None and extremum_d_ptime > first_cd_ptime:
                    if self.breakthrough_direction == Constants.DIRECTION_UP:
                        # if cd.close < self.extremum_d.low:
                        if cd.close < self.last_cd.low:
                            self.effective_extremum_d = deepcopy(self.extremum_d)
                            self.effective_extremum_d.bk_type = Constants.BK_TYPE_OF_NONE
                            self.effective_extremum_d.tag = True
                            self.effective_extremum_d_price = self.extremum_d_price
                            self.set_ir_last(effective=True)
                            # print(f"设置有效d => effective_cr_obj => {self.effective_cr_obj} \ncr_list => {self.effective_cr_list} \neffective_extremum_d => {self.effective_extremum_d} \ncd => {cd} \nir_last => {self.effective_ir_last} \neffective_extremum_d_price => {self.effective_extremum_d_price}")
                    elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                        # if cd.close > self.extremum_d.high:
                        if cd.close > self.last_cd.high:
                            self.effective_extremum_d = deepcopy(self.extremum_d)
                            self.effective_extremum_d.bk_type = Constants.BK_TYPE_OF_NONE
                            self.effective_extremum_d.tag = True
                            self.effective_extremum_d_price = self.extremum_d_price
                            self.set_ir_last(effective=True)
                            # print(f"设置有效d => effective_cr_obj => {self.effective_cr_obj} \ncr_list => {self.effective_cr_list} \neffective_extremum_d => {self.effective_extremum_d} \ncd => {cd} \nir_last => {self.effective_ir_last} \neffective_extremum_d_price => {self.effective_extremum_d_price}")
                            
    """
    出现IR>IRlast（IR>10）突破D视为有效突破，有效突破后有效D随之变化，否则就是无效突破
    无效突破后续判断是否进入有效回归，如果满足有效回归就开车
    """
    def handle_breakthrough(self, cd):
        if self.effective_extremum_d_price is not None and self.breakthrough_direction == self.current_ir.direction:
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if self.current_ir.end_price > self.effective_extremum_d_price > self.current_ir.start_price:
                    if self.current_ir.length > self.effective_ir_last.length:
                        # 去掉有效D
                        self.reset_effective_extremum_d()
                        self.effective_break_through_datetime = cd.datetime
                        # print(f"有效突破 cd => {cd} \neffective_cr_list => {self.effective_cr_list} \neffective_ir_last => {self.effective_ir_last} \ncurrent_cr => {self.current_ir}")
                    else:
                        # 给有效D打上无效突破的标记
                        if self.effective_extremum_d.bk_type == Constants.BK_TYPE_OF_NONE:
                            self.effective_extremum_d.bk_type = Constants.BK_TYPE_OF_INEFFECTIVE
            elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                if self.current_ir.start_price > self.effective_extremum_d_price > self.current_ir.end_price:
                    if self.current_ir.length > self.effective_ir_last.length:
                        self.reset_effective_extremum_d()
                        self.effective_break_through_datetime = cd.datetime
                        # print(f"有效突破 cd => {cd} \neffective_cr_list => {self.effective_cr_list} \neffective_ir_last => {self.effective_ir_last} \ncurrent_cr => {self.current_ir}")
                    else:
                        if self.effective_extremum_d.bk_type == Constants.BK_TYPE_OF_NONE:
                            self.effective_extremum_d.bk_type = Constants.BK_TYPE_OF_INEFFECTIVE
    
    """
    有效无序
    突破有效趋势起点视为无序，此时无有效加速
    """
    def handle_effective_disorder(self, cd):
        if self.effective_cr_obj is not None:
            if self.effective_cr_obj.direction == Constants.DIRECTION_UP:
                if cd.low < self.effective_cr_obj.start_price:
                    self.reset_effective_cr()
            elif self.effective_cr_obj.direction == Constants.DIRECTION_DOWN:
                if cd.high > self.effective_cr_obj.start_price:
                    self.reset_effective_cr()

    """
    重置有效D
    """
    def reset_effective_extremum_d(self):
        self.effective_extremum_d = None
        self.effective_extremum_d_price = None
        # 充值有效小cr为None
        self.reset_effective_lowercase_cr()

    """
    设置ir_last
    """
    def set_ir_last(self, effective=False):
        # 设置ir_last
        if self.current_ir.direction == self.breakthrough_direction and self.current_ir.length > 10*self.unit_value:
            self.ir_last = self.current_ir
        # 讲ir_last设置为有效ir_last
        if effective:
            self.effective_ir_last = self.ir_last

    """
    协定ir
    当ir的长度大于指定单位，并且突破d时
    """
    def handle_agreement_ir(self, cd):
        if self.is_equal_d_price(cd):
            if self.current_ir.length > 20*self.unit_value and self.current_ir.direction == self.breakthrough_direction:
                self.agreement_ir = deepcopy(self.current_ir)
                self.agreement_ir.tag = True

    """
    方向处理
    当出现最大的CRmax时，调整方向跟最大的CRmax一致
    当回归到CRmax的起点时，改变方向跟CRmax方向相反
    当方向跟CRmax方向相反时，回到CRmax的终点时调整方向跟CRmax方向一致
    """
    def handle_direction(self, cd):
        # 刷新CRmax
        if self.max_cr_obj is not None and self.cr_obj is not None: 
            if self.max_cr_obj.length == self.cr_obj.length:
                if not self.breakthrough_direction == self.cr_obj.direction:
                    self.breakthrough_direction = self.cr_obj.direction
                    self.on_direction_change(cd)
            else:
                if Logic.is_exceed_max_cr_start_price(self.breakthrough_direction, self.max_cr_obj, cd):
                    self.reverse_direct_by_max_cr()
                    self.on_direction_change(cd)
                    # 设置成不能开仓状态
                    self.handle_allow_open_by_rc_start_cd()
                    # print(f"回落到起点 => cd => {cd} max_cr_obj => {self.max_cr_obj}")
                    # self.reset_max_cr()
                    self.reset_change_direction_number()
                elif Logic.is_exceed_max_cr_end_price(self.breakthrough_direction, self.max_cr_obj, cd):
                    self.set_direction_by_max_cr()
                    self.on_direction_change(cd)
                    # print(f"回落到起点 => cd => {cd} max_cr_obj => {self.max_cr_obj}")

    """
    跌落起点，不允许开仓
    """
    def handle_allow_open_by_rc_start_cd(self):
        self.allow_open = False
    
    """
    跌落起点，不允许开仓
    """
    def handle_allow_open_by_cr_refresh(self):
        self.allow_open = True
    
    """
    重置cr
    """
    def reset_max_cr(self):
        self.max_cr_list = []
        self.max_cr_obj = None

    """
    将开仓机会重置为0
    """    
    def reset_change_direction_number(self):
        self.change_direction_number = 0
                
    """
    超过限定时间，设置ml
    """ 
    def over_interval_minutes(self, cd):
        current_date = datetime.strptime(cd.datetime, "%Y-%m-%d %H:%M:%S")
        l_date = datetime.strptime(self.extremum_l.datetime, "%Y-%m-%d %H:%M:%S")

        if (current_date - l_date).seconds >= self.interval_minutes * 60:
            return True
        else:
            return False

    """
    开多情况，如果比上一分钟的低点低为真
    开空情况，如果比上一分钟的高点高为真
    """
    def is_exceed_last_cd_high(self,cd):
        if self.trade_action == Constants.ACTION_OPEN_LONG:
            if cd.low < self.last_cd.low:
                return True
        elif self.trade_action == Constants.ACTION_OPEN_SHORT: 
            if cd.high > self.last_cd.high:
                return True
        return False
    
    """
    开多情况，如果比上一分钟的高点高为真
    开空情况，如果比上一分钟的低点低为真
    """
    def is_exceed_last_cd_low(self, cd):
        if self.trade_action == Constants.ACTION_OPEN_LONG:
            if cd.high > self.last_cd.high:
                return True
        elif self.trade_action == Constants.ACTION_OPEN_SHORT: 
            if cd.low < self.last_cd.low:
                return True
        return False

    """
    处理最大的幅度区间Rmax
    """    
    def handle_max_amplitude(self, cd):
        appear = False
        if self.max_l_to_d_interval.length >= self.max_r.length:
            if self.max_l_to_d_interval.length > self.max_amplitude.length:
                self.max_amplitude.direction = self.max_l_to_d_interval.direction
                self.max_amplitude.real_direction = self.breakthrough_direction
                self.max_amplitude.start = self.max_l_to_d_interval.start_price            
                self.max_amplitude.end = self.max_l_to_d_interval.end_price
                self.max_amplitude.length = abs(self.max_amplitude.start - self.max_amplitude.end)
                self.max_amplitude.datetime = cd.datetime
                appear = True
        else:
            if self.max_r.length > self.max_amplitude.length:
                self.max_amplitude.direction = self.max_r.direction 
                self.max_amplitude.real_direction = self.breakthrough_direction
                self.max_amplitude.start = self.max_r.start_price
                self.max_amplitude.end = self.max_r.end_price
                self.max_amplitude.length = abs(self.max_amplitude.start - self.max_amplitude.end)
                self.max_amplitude.datetime = cd.datetime
                appear = True
        if appear:
            # 重置R
            self.max_l_to_d_interval = None
            # 重置r
            self.max_r = None
    
    """
    统计cr_list区间最大的
    目前统计的都是跟cr_obj同一个方向
    """
    def handle_max_ir_by_cr(self):
        if self.current_ir is not None and self.cr_obj is not None:
            if self.current_ir.direction == self.cr_obj.direction:
                if self.max_ir_by_cr is None or (self.current_ir.length > self.max_ir_by_cr.length):
                    self.max_ir_by_cr = deepcopy(self.current_ir)
    
    """
    设置当前的ir,比较 current_max_l_to_d_interval 跟 current_max_r的大小，大者为当前ir
    """
    def handle_current_ir(self, cd):
        self.current_ir = QuotationLogic.get_current_ir(self.breakthrough_direction, self.last_cd, cd)
        # print(f"current_ir => {self.current_ir}")
                
    """
    方向改变执行的动作
    重置d
    重置l
    重置rrn
    """
    def on_direction_change(self, cd):
        # 重置d
        self.reset_extremum_d()
        self.set_extremum_d(cd)
        # 重置l
        self.reset_extremum_l()
        # 重置rrn
        self.rrn = None
        # 重置有效cr
        self.reset_effective_cr()

    
    """
    趋势分析
    """
    def history_statistic_max_l_to_d(self, cd):
        max_l_to_d_obj = QuotationLogic.get_max_l_to_d(self.breakthrough_direction, self.last_cd, cd)
        # 判断是否出现极值d点
        if self.exceed_extremum_d(cd):
            # 设置点D
            self.set_extremum_d(cd)
        else:
            # 设置D的起点
            self.set_d_start_cd(cd)

            self.set_rrn(max_l_to_d_obj.length)
            # 设置extremum_l
            self.set_extremum_l(cd)

        # 记录下当前的max_l_to_d
        max_l_to_d_obj.datetime = cd.datetime
        self.current_max_l_to_d_interval = max_l_to_d_obj
        # 记录最大的max_l_to_d
        self.set_max_l_to_d_interval_obj(max_l_to_d_obj)


    """
    开始点设置R
    """ 
    def first_l_to_d(self, cd):
        obj = None
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.direction == Constants.DIRECTION_UP:
                obj = QuotationLogic.amplitude_obj(cd.low, cd.high)
            else:
                obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
        else:
            if cd.direction == Constants.DIRECTION_UP:
                obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
            else:
                obj = QuotationLogic.amplitude_obj(cd.high, cd.low)
        return obj

    """
    分析统计最大的max_r
    """
    def history_statistic_max_r(self, cd): 
        max_r_obj = QuotationLogic.get_max_r(self.breakthrough_direction, self.last_cd, cd)
        # 添加一个时间
        max_r_obj.datetime = cd.datetime
        self.set_max_r(max_r_obj) 
        self.current_max_r = max_r_obj
        # self.set_max_lowercase_ir_by_max_r(cd)

    """
    设置走势方向
    设置最大的幅度，包括开始价、结束价，幅度值
    """
    def init_set_max_amplitude(self, cd):
        # 十字星就将方向定义跟主程序方向一致
        if Logic.is_crossing_starlike(cd):
            cd.direction = self.breakthrough_direction
        # 当前点的方向决定走势方向
        current = SimpleNamespace()
        current.length = Logic.max_amplitude_length(cd)
        current.direction = cd.direction
        current.datetime = cd.datetime
        if cd.direction == Constants.DIRECTION_UP:
            current.start = cd.low
            current.end = cd.high
        else:
            current.start = cd.high
            current.end = cd.low

        # 在主程序没有方向，其实就是昨日收盘价跟今日开盘价想等的时候
        if self.breakthrough_direction is None:
            self.breakthrough_direction = cd.direction
        current.real_dirction = self.breakthrough_direction
        self.max_amplitude = current
        self.last_max_amplitude = deepcopy(self.max_amplitude)

    """
    设置最小的ln
    """

    def set_lowest_point_l(self, cd):
        if self.lowest_point_l is None:
            self.lowest_point_l = cd
        else:
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if cd.low < self.lowest_point_l.low:
                    self.lowest_point_l = cd
            else:
                if cd.high > self.lowest_point_l.high:
                    self.lowest_point_l = cd

    """
    设置最大的dn_to_ln
    当dn_to_ln_max的值为None的时候，设置为极致点D对应数值
    """
    def set_max_r(self, obj):
        if self.max_r == None or self.max_r.length < obj.length:
            self.max_r = obj

    """
    设置小级别的m_max_r
    """
    def set_m_max_r(self, obj):
        if self.m_max_r == None or self.m_max_r.length < obj.length:
            self.m_max_r = obj

    """
    获取逆趋势的平仓价格
    """

    def get_counter_trend_close_a_position_price(self, cd):
        d_close_price = self.reference_point_d.close
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            close_a_position_price = cd.high - self.b1_to_b2_interval
            close_a_position_price = max(d_close_price, close_a_position_price)
            if cd.high < d_close_price:
                close_a_position_price = cd.high
        else:
            close_a_position_price = cd.low + self.b1_to_b2_interval
            close_a_position_price = min(d_close_price, close_a_position_price)
            if cd.low > close_a_position_price:
                close_a_position_price = cd.low

        return close_a_position_price

    """
    是否可以给逆趋势平仓
    如果是相同方向就不平仓，
    否则如果当前一分钟的高价大于参考点D的结束价（平仓价位）且低点小于D点的结束价就平仓
    """

    def can_close_a_position_for_counter_trend(self, cd):
        if self.is_same_direction(cd):
            current_amplitude_length = Logic.amplitude_length(cd, self.breakthrough_direction)
        else:
            current_amplitude_length = Logic.max_amplitude_length(cd)
        if cd.high > self.reference_point_d.close > cd.low or current_amplitude_length > self.b1_to_b2_interval:
            return True
        else:
            return False

    """
    获取情况一开仓价格
    """

    def get_situation1_open_a_position_price(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            return max(self.reference_point_d.high, cd.low)
        else:
            return min(self.reference_point_d.low, cd.high)

    """
    是否出现极值
    """

    def exceed_extremum_d(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.high >= self.extremum_d_price:
                return True
            else:
                return False
        else:
            if cd.low <= self.extremum_d_price:
                return True
            else:
                return False
    
    """
    等于D的价格
    """
    def is_equal_d_price(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.high == self.extremum_d_price:
                return True
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            if cd.low == self.extremum_d_price:
                return True
        
        return False

    """
    改变方向
    """

    def reverse_direct(self):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            self.breakthrough_direction = Constants.DIRECTION_DOWN
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            self.breakthrough_direction = Constants.DIRECTION_UP

    """
    改变方向
    """
    def reverse_direct_by_max_amplitude(self):
        if self.max_amplitude.direction == Constants.DIRECTION_UP:
            self.breakthrough_direction = Constants.DIRECTION_DOWN
            self.max_amplitude.real_direction = self.breakthrough_direction
        elif self.max_amplitude.direction == Constants.DIRECTION_DOWN:
            self.breakthrough_direction = Constants.DIRECTION_UP
            self.max_amplitude.real_direction = self.breakthrough_direction
    
    """
    改变方向
    """
    def reverse_direct_by_max_cr(self):
        if self.max_cr_obj.direction == Constants.DIRECTION_UP:
            self.breakthrough_direction = Constants.DIRECTION_DOWN
        elif self.max_cr_obj.direction == Constants.DIRECTION_DOWN:
            self.breakthrough_direction = Constants.DIRECTION_UP

    """
    通过max_amplitude制定方向
    """
    def set_direction_by_max_cr(self):
        self.breakthrough_direction = self.max_cr_obj.direction

    """
    通过max_amplitude制定方向
    """
    def set_direction_by_max_amplitude(self):
        self.breakthrough_direction = self.max_amplitude.direction
        self.max_amplitude.real_direction = self.breakthrough_direction

    """
    没有试错机会重新开始
    """

    def restart(self):
        self.reference_point_d = None  # 振荡的参考点D
        self.extremum_d_price = None  # 设置极值d_price为None
        self.breakthrough_direction = None  # 突破的方向 -1 向下 1 向上
        self.max_l_to_d_interval = None  # 最大上涨的间隔
        self.current_status = Constants.STATUS_NONE  # 当前状态
        self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_NO  # 振荡检测
        self.max_r = None
        self.rrn = None 
        self.history_status = Constants.HISTORY_STATUS_OF_NONE # 历史分析状态

    """
    判断当前方向是否跟突破后的方向一致
    在开多情况下，如果当前点是上涨就为True
    在开空情况下，如果当前点是下跌就为True
    """
 
    def is_same_direction(self, cd):
        if cd.direction == Constants.DIRECTION_UP and self.breakthrough_direction == Constants.DIRECTION_UP:
            return True
        elif cd.direction == Constants.DIRECTION_DOWN and self.breakthrough_direction == Constants.DIRECTION_DOWN:
            return True
        else:
            return False

    """
    bar数据实时分析    
    """
    def realtime_analysis(self, bar):
        cd = Logic.bar_to_data_object(bar)
        self.realtime_analysis_for_cd(cd)

    """  
    用cd数据格式进行分析
    """   
    def realtime_analysis_for_cd(self, cd):
        # 十字星情况，将方向设置为跟上一分钟一致
        if Logic.is_crossing_starlike(cd):
            if self.last_cd is not None and not self.last_cd.direction == Constants.DIRECTION_NONE:
                cd.direction = self.last_cd.direction
 
        if self.history_status == Constants.HISTORY_STATUS_OF_NONE: 
            # 初始化起点
            if self.start_cd is None:
                self.start_cd = cd
            self.get_fictitious_cd()
            if self.fictitious_cd is not None:
                self.histoty_status_none(self.fictitious_cd)
                self.handle_cr_list(self.fictitious_cd)
                self.handle_ir_by_histoty_status_none(self.fictitious_cd)
                self.init_current_ir(self.fictitious_cd)
                self.handle_effective_trend()
            if self.history_status == Constants.HISTORY_STATUS_OF_NONE:
                self.histoty_status_none(cd)
                # 统计连续的幅度
                self.handle_cr_list(cd)
                self.handle_ir_by_histoty_status_none(cd)
                self.handle_effective_trend()
            elif self.history_status == Constants.HISTORY_STATUS_OF_TREND:
                # 统计连续的幅度
                self.handle_cr_list(cd)
                self.last_cd = deepcopy(self.fictitious_cd)
                self.statistic(cd)
                # print(f"跑到这里 {self.fictitious_cd} {self.breakthrough_direction} {self.max_cr_list} l => {self.extremum_l} d => {self.extremum_d}")
                # sys.exit(1)

            # print(f"完成状态初始化 => yesterday_close_price => {self.yesterday_close_price} start_cd => {self.start_cd} , breakthrough_direction => {self.breakthrough_direction} max_amplitude => {self.max_amplitude} extremum_d => {self.extremum_d}")
        elif self.history_status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
            cd_time = Logic.ptime(cd.datetime)
            if cd_time.hour == 9 and cd_time.minute == 0:
                fictitious_cd = Logic.get_fictitious_cd(self.last_cd, cd)
                # 统计连续的幅度
                self.handle_cr_list(fictitious_cd)
                self.statistic(fictitious_cd)
                self.last_cd = Logic.handle_last_cd(self.last_cd, fictitious_cd)

            # 统计连续的幅度
            self.handle_cr_list(cd)
            self.statistic(cd)
        # 判断是否需要合并,当当前分钟为直线时考虑
        self.last_cd = Logic.handle_last_cd(self.last_cd, cd)

    def init_current_ir(self, fictitious_cd):
        self.current_ir = QuotationLogic.amplitude_obj(fictitious_cd.open, fictitious_cd.close)

    """
    在没有进入行情的时候处理ir
    """
    def handle_ir_by_histoty_status_none(self, cd):
        if self.breakthrough_direction is not None and not Logic.is_crossing_starlike(cd):
                if cd.direction == Constants.DIRECTION_UP:
                    start_price = cd.low
                    end_price = cd.high
                    self.max_ir_by_cr = QuotationLogic.amplitude_obj(start_price, end_price)
                else:
                    start_price = cd.high
                    end_price = cd.low
                    self.max_ir_by_cr = QuotationLogic.amplitude_obj(start_price, end_price)
  
                self.max_ir_by_cr.datetime = cd.datetime
    

    # 将昨日收盘价跟今日开盘模拟成一分钟
    def get_fictitious_cd(self):
        if self.fictitious_cd is None:
            self.fictitious_cd = SimpleNamespace()
            self.fictitious_cd.open = self.yesterday_close_price
            self.fictitious_cd.close = self.start_cd.open
            self.fictitious_cd.high = max(self.fictitious_cd.open, self.fictitious_cd.close)
            self.fictitious_cd.low = min(self.fictitious_cd.open, self.fictitious_cd.close)  
            self.fictitious_cd.datetime = self.start_cd.datetime # 用开始的一分钟时间 
            if self.start_cd.open > self.yesterday_close_price:
                self.fictitious_cd.direction = Constants.DIRECTION_UP
                self.breakthrough_direction = Constants.DIRECTION_UP
            elif self.start_cd.open < self.yesterday_close_price:
                self.fictitious_cd.direction = Constants.DIRECTION_DOWN
                self.breakthrough_direction = Constants.DIRECTION_DOWN
            else:
                self.fictitious_cd.direction = Constants.DIRECTION_NONE
            if self.breakthrough_direction is None:
                self.breakthrough_direction = self.fictitious_cd.direction

    """
    将昨日的max_cr相关的参数设置到今天
    """
    def init_max_cr(self):
        if self.last_history is not None and self.max_cr_obj is None:
            self.max_cr_list = deepcopy(self.last_history.max_cr_list)
            self.max_cr_obj = deepcopy(self.last_history.max_cr_obj)

    """
    将昨日的d设置到程序中
    """ 
    def init_extremum_d(self):
        if self.last_history is not None and self.last_history.extremum_d is not None:
            self.extremum_d = deepcopy(self.last_history.extremum_d)
            self.extremum_d_price = self.last_history.extremum_d_price

    """
    处理连续行情数据
    """
    def handle_cr_list_old(self, cd):
        # 将昨日的max_cr相关初始化到今天
        if not Logic.is_crossing_starlike(cd):
            if len(self.cr_list) == 0:
                self.cr_list.append(cd)
                # print(f"将开盘的幅度统计进去 {self.cr_list} yesterday_close_price => {self.yesterday_close_price} => cd => {cd}")
            elif len(self.cr_list) > 0:
                temp_last_cd = self.cr_list[-1]
                if not cd.direction == temp_last_cd.direction:
                    self.cr_list = []
                    # 重置ir
                    self.max_ir_by_cr = None 
                self.cr_list.append(cd)
            
            if len(self.cr_list) > 0:
                temp_start_cd = self.cr_list[0]
                temp_end_cd = self.cr_list[-1]
                temp_direciton = temp_start_cd.direction
                if self.cr_obj is None:
                    self.cr_obj = SimpleNamespace()
                if temp_direciton == Constants.DIRECTION_UP:
                    self.cr_obj.start_price = temp_start_cd.low
                    self.cr_obj.end_price = temp_end_cd.high
                    self.cr_obj.length = abs(temp_end_cd.high - temp_start_cd.low)
                    self.cr_obj.direction = temp_direciton
                elif temp_direciton == Constants.DIRECTION_DOWN:
                    self.cr_obj.start_price = temp_start_cd.high
                    self.cr_obj.end_price = temp_end_cd.low
                    self.cr_obj.length = abs(temp_start_cd.high - temp_end_cd.low)
                    self.cr_obj.direction = temp_direciton
                if self.cr_obj is not None and (self.max_cr_obj is None or self.cr_obj.length > self.max_cr_obj.length):
                    self.max_cr_obj = deepcopy(self.cr_obj)
                    self.max_cr_list = deepcopy(self.cr_list)

    """
    处理连续行情数据
    """
    def handle_cr_list(self, cd):
        # 初始化当前cr_obj
        if self.cr_obj is None:
            self.cr_list, self.cr_obj = QuotationLogic.get_cr_information(cd, [], None)
        else:
            if self.temp_cr_obj is None:
                if not cd.direction == self.cr_obj.direction:
                    self.temp_cr_list, self.temp_cr_obj = QuotationLogic.get_cr_information(cd, [], None)
            else:
                self.temp_cr_list, self.temp_cr_obj = QuotationLogic.get_cr_information(cd, self.temp_cr_list, self.temp_cr_obj)
            # print(f"before => cr_list => {self.cr_list}  \ncr_obj => {self.cr_obj}  \ncd => {cd} \n")
            self.cr_list, self.cr_obj = QuotationLogic.get_cr_information(cd, self.cr_list, self.cr_obj)
            if self.cr_obj is None:
                self.cr_list = deepcopy(self.temp_cr_list)
                self.cr_obj = deepcopy(self.temp_cr_obj)
                self.reset_temp_cr()
                # todo 设置max_ir_by_cr 为None
                self.max_ir_by_cr = QuotationLogic.get_max_ir_by_cr_list(self.cr_list)
                # print(f"after => cr_list => {self.cr_list}  \ncr_obj => {self.cr_obj}  \ncd => {cd} \n tmp_cr_list => {self.temp_cr_list} temp_cr_obj => {self.temp_cr_obj}")

        # 设置最大的max_cr
        if self.cr_obj is not None and (self.max_cr_obj is None or self.cr_obj.length > self.max_cr_obj.length):
            self.max_cr_obj = deepcopy(self.cr_obj)
            self.max_cr_list = deepcopy(self.cr_list)
    
    """
    重置temp_cr
    """
    def reset_temp_cr(self):
        self.temp_cr_list = []
        self.temp_cr_obj = None


    """
    实时分析    
    """
    def realtime_analysis1(self, cd):
        if Logic.is_start_minute(cd.datetime):
            return
        if self.history_status == Constants.HISTORY_STATUS_OF_NONE: 
            self.histoty_status_none(cd)
        elif self.history_status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
            self.statistic(cd)
        # 判断是否需要合并,当当前分钟为直线时考虑
        self.last_cd = Logic.handle_last_cd(self.last_cd, cd)
        self.refresh_d_minute_count += 1
        self.refresh_h_minute_count += 1