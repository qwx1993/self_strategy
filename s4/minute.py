"""
main.py
读取data文件夹中的所有csv文件，针对每个文件计算出该交易策略的胜率和赚钱点数
"""
import os
import sys
from self_strategy.constants import Constants
from self_strategy.constants_s3 import ConstantsS3 as S3_Cons
from self_strategy.logic import Logic
from types import SimpleNamespace
# 
class Minute:
    breakthrough_direction = None # 突破的方向 -1 开空 1开多

    stop_loss_ln_price = None  # 情况三的止损点价位 L - 2*unit

    max_l_to_d_interval = None  # 最大上涨的间隔,即R
    current_max_l_to_d_interval = None # 当前的上涨间隔
    max_r = None  # 表示从dn-ln的最大值，d1点开始
    rrn = None  # 逆趋势止盈使用的参数  todo 暂时不使用

    current_status = Constants.STATUS_NONE  # 当前状态，目前就无状态跟非加速振荡

    counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态，默认非逆趋势状态
    sub_status = S3_Cons.SUB_STATUS_OF_NONE # 策略三的子状态

    actions = []  # 记录所有的动作，包括开空，开多，逆开空，逆开多，注意：逆趋势下是两倍仓位
    test_need_statistic = False # 测试是否需要统计   
    extremum_d_price = None  # 极致d的price
    extremum_d = None  # 极值点D
    extremum_l_price = None # 极值点l的price
    extremum_l = None # 极值点l

    h_price = None # h点，表示比仅次于d点第二高点

    history_status = Constants.HISTORY_STATUS_OF_NONE # 历史状态
    last_cd = None # 上一点
    max_amplitude = None # 最大幅度对象
    h_price_max = None # h的极值
    trade_action = None
    ml = None # 出现小级别逆趋势后的低点，需比L的值大
    ml_1_price  = None # 用于止盈
    m_max_r = None  # 小级别r
    M_MAX_R = None  # 小级别R
    agreement_close_price = None # 预估平仓价
    close_price = None # 平仓价
    unit_value = 0 # 单位值
    max_limit = 2 # 满足开仓条件后
    has_open_a_position_times = 0 # 已开仓次数

    """
    初始化
    """

    def __init__(self):
        # 所有的list跟dict需要重置
        self.max_l_to_d_interval = None
        self.max_r = None
        self.actions = []
        self.max_amplitude = None
        self.m_max_r = None  # 小级别r
        self.M_MAX_R = None  # 小级别R


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
    设置子状态
    """
    def set_sub_status(self, sub_status):
        self.sub_status = sub_status

    """
    设置当前是否为逆趋势中， 包括两种状态，逆趋势状态、非逆趋势状态
    """

    def set_counter_trend_status(self, status):
        self.counter_trend_status = status

    """
    设置最大的l_to_d间隔数据
    """

    def set_max_l_to_d_interval_obj(self, obj):
        if (self.max_l_to_d_interval is None) or (obj.length > self.max_l_to_d_interval.length):
            self.max_l_to_d_interval = obj

    """
    设置小级别的M_MAX_R
    """
    def set_M_MAX_R_obj(self, obj):
        if (self.M_MAX_R is None) or (obj.length > self.M_MAX_R.length):
            self.M_MAX_R = obj

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
        self.extremum_d = dn
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if (self.extremum_d_price is None) or dn.high > self.extremum_d_price:
                self.extremum_d_price = dn.high
                
        else:
            if (self.extremum_d_price is None) or dn.low < self.extremum_d_price:
                self.extremum_d_price = dn.low
    
    """
    重新设置极值d
    """
    def reset_extremum_d(self):
        self.extremum_d = None
        self.extremum_d_price = None

    """
    设置l1的相关值
    """
    def set_extremum_l(self, ln):
        if self.extremum_d_price is not None:
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if (self.extremum_l_price is None) or ln.low < self.extremum_l_price:
                    self.extremum_l_price = ln.low
                    self.extremum_l = ln
                    self.after_set_extremum_l(ln)
                    # print(f"出现新的l => {ln.datetime} extremum_d_price => {self.extremum_d_price}")
                else:
                    # 如果是L状态，就设置为逆趋势状态
                    if self.sub_status == S3_Cons.SUB_STATUS_OF_L:
                        self.set_sub_status(S3_Cons.SUB_STATUS_OF_TREND_COUNTER)
            else:
                if (self.extremum_l_price is None) or ln.high > self.extremum_l_price:
                    self.extremum_l_price = ln.high
                    self.extremum_l = ln
                    self.after_set_extremum_l(ln)
                    # print(f"出现新的l => {ln.datetime} extremum_d_price => {self.extremum_d_price}")
                else:
                    if self.sub_status == S3_Cons.SUB_STATUS_OF_L:
                        self.set_sub_status(S3_Cons.SUB_STATUS_OF_TREND_COUNTER)

    """
    设置极值L后的动作，设置状态为L
    将策略三相关的参数设置为None
    """
    def after_set_extremum_l(self, cd):
        # 设置L为最新的状态
        self.set_sub_status(S3_Cons.SUB_STATUS_OF_L)
        self.m_max_r = None
        self.M_MAX_R = self.first_l_to_d(cd) 
        self.ml = None
        # 出现新的l刷新开仓次数
        self.has_open_a_position_times = 0

    """
    重置extremum_l的值
    """
    def reset_extremum_l(self):
        self.extremum_l = None
        self.extremum_l_price = None
        # 重置开盘次数
        self.has_open_a_position_times = 0
    
    """
    设置h_price参数
    """
    def set_h_price(self, cd):
        if self.extremum_d_price is not None and Logic.is_high_point(self.breakthrough_direction, self.last_cd, cd):
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if (self.h_price is None) or cd.high > self.h_price:
                    self.h_price = cd.high
                    if (self.h_price_max is None) or self.h_price > self.h_price_max:
                        self.h_price_max = self.h_price
            elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                if (self.h_price is None) or cd.low < self.h_price:
                    self.h_price = cd.low
                    if (self.h_price_max is None) or self.h_price < self.h_price_max:
                        self.h_price_max = self.h_price

    """
    设置ml的price
    """   
    def set_ml_price(self, cd):
        refresh_ml = False
        if self.extremum_l_price is not None and Logic.is_low_point(self.breakthrough_direction, self.last_cd, cd):
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if (self.ml is None) or cd.low < self.ml:
                    self.ml = cd.low
                    # print(f"设置ml1 => {self.ml} {cd.datetime}")
                    refresh_ml = True
            elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                if (self.ml is None) or cd.high > self.ml:
                    self.ml = cd.high
                    # print(f"设置ml-1 => {self.ml} {cd.datetime}")
                    refresh_ml = True
        # 存在ml就判断是否可以开仓
        if self.ml is not None and not refresh_ml:
            self.handle_open_a_price(cd)
    
    """
    开仓位出现后设置ml_1_price
    """
    def set_ml_1_price(self, cd):
        if Logic.is_low_point(self.breakthrough_direction, self.last_cd, cd):
            if (self.ml_1_price is None) or cd.low > self.ml_1_price:
                self.ml_1_price = cd.low
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            if (self.ml_1_price is None) or cd.high < self.ml_1_price:
                self.ml_1_price = cd.high

    """
    重新设置ml_1_price为None
    """
    def reset_ml_1_price(self):
        self.ml_1_price = None

    """
    出现ml1就开仓，否则不开仓
    """ 
    def handle_open_a_price(self, cd):
        if self.find_open_a_price(cd):
            self.set_open_trade_action()
            self.set_sub_status(S3_Cons.SUB_STATUS_OF_ML_ONE)

            # 分钟测试时才需要的代码
            if self.trade_action == Constants.ACTION_OPEN_LONG:
                open_a_price = self.last_cd.high
                self.close_price = self.last_cd.low
            elif self.trade_action == Constants.ACTION_OPEN_SHORT:
                open_a_price = self.last_cd.low
                self.close_price = self.last_cd.high
            self.add_action(cd, self.trade_action, open_a_price)
            
            print(f"Rmax => {self.max_amplitude}")
            print(f"进入ml1开仓 {cd.datetime} 开仓价{self.last_cd} ---------------------------------------------------------------------------------------")
            print(f"l => {self.extremum_l_price}")   
            print(f"ml => {self.ml}")
            print(f"开仓方向 => {self.breakthrough_direction}")
            print(f"M_MAX_R => {self.M_MAX_R}")   
            print(f"m_max_r => {self.m_max_r} -------------------------------------------------------------------------------------")   

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
    def find_open_a_price(self, cd):
        if self.ml is not None:
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if cd.high > self.last_cd.high:
                    return True
            elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
                if cd.low < self.last_cd.low:
                    return True
        return False

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

    """
    当前状态为STATUS_NONE时的逻辑
    """

    def histoty_status_none(self, cd):
        # 初始化时为十字星不处理
        if Logic.is_crossing_starlike(cd):
            return

        # 设置走势方向，设置最大的幅度对象，包括最大幅度的起始、结束值跟幅度
        self.init_set_max_amplitude(cd)
        # 设置最大的上涨幅度
        self.max_l_to_d_interval = None
        # self.init_max_l_to_d_interval_obj(cd)
        # 初始化最大的下降幅度
        self.max_r = None
        # self.init_max_r_obj(cd)
        # 设置参考点d
        self.reference_point_d = cd
        # 设置极限d_price
        self.extremum_d_price = None
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
            max_l_to_d_obj = self.amplitude_obj(cd.low, cd.high)
        else:
            max_l_to_d_obj = self.amplitude_obj(cd.high, cd.low)
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
                max_r_obj = self.amplitude_obj(cd.open, cd.low)
            else:
                max_r_obj = self.amplitude_obj(cd.high, cd.close)
        else:
            len = abs(cd.high - cd.open)
            end_len = abs(cd.close - cd.low)

            if len > end_len:
                max_r_obj = self.amplitude_obj(cd.open, cd.high)
            else:
                max_r_obj = self.amplitude_obj(cd.low, cd.close)
        self.max_r = max_r_obj

    """
    分析统计R、r、rrn
    """
    def statistic(self, cd):
        # 十字星情况，将方向设置为跟上一分钟一致
        if Logic.is_crossing_starlike(cd):
            cd.direction = self.last_cd.direction
        # 统计R、统计rrn
        self.history_statistic_max_l_to_d(cd)

        # 统计r
        self.history_statistic_max_r(cd)
        # 处理出现最大的幅度情况
        self.handle_max_amplitude(cd)
        # 逆趋势判断
        if Logic.is_counter_trend1(self.M_MAX_R, self.m_max_r) and self.sub_status == S3_Cons.SUB_STATUS_OF_TREND_COUNTER:
            # print(f"出现逆趋势 => {cd.datetime}")
            self.set_sub_status(S3_Cons.SUB_STATUS_OF_ML)
        if self.sub_status == S3_Cons.SUB_STATUS_OF_ML:
            # 设置ml
            self.set_ml_price(cd)

        # 开仓状态管理
        if self.trade_action in [Constants.ACTION_OPEN_LONG, Constants.ACTION_OPEN_SHORT]:
            if self.close_a_price(cd):
                self.close_a_price_by_last_cd_low_price(cd)
            elif self.is_exceed_last_cd_high(cd):
                self.set_agreement_close_price(cd)
            elif self.is_exceed_last_cd_low(cd):
                self.set_close_price_by_agreement()

    """
    平仓通过上一分钟的最低价
    """
    def close_a_price_by_last_cd_low_price(self, cd):
        if self.trade_action == Constants.ACTION_OPEN_LONG:
            if self.close_price > cd.low:
                self.trade_action = Constants.ACTION_CLOSE_LONG
                # 临时使用
                if self.test_need_statistic:
                    self.add_action(cd, self.trade_action, self.close_price - self.unit_value)
                print(f"平仓1 => {cd.datetime} {self.close_price - self.unit_value}")
                if self.sub_status == S3_Cons.SUB_STATUS_OF_ML_ONE:
                    self.reset_params_by_close_a_price()
        elif self.trade_action == Constants.ACTION_OPEN_SHORT:
            if self.close_price < cd.high:
                print(f"平仓2 => {cd.datetime} 平仓价格 => {self.close_price + self.unit_value}")
                self.trade_action = Constants.ACTION_CLOSE_SHORT
                # 临时使用
                if self.test_need_statistic:
                    self.add_action(cd, self.trade_action, self.close_price + self.unit_value)
                if self.sub_status == S3_Cons.SUB_STATUS_OF_ML_ONE:
                    self.reset_params_by_close_a_price()
    
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
    设置开仓协定价格
    """
    def set_close_price_by_agreement(self):
        if self.agreement_close_price is not None:
            self.close_price = self.agreement_close_price
            self.agreement_close_price = None

    def set_agreement_close_price(self, cd):
        if self.trade_action == Constants.ACTION_OPEN_LONG:
            if self.agreement_close_price is None or cd.low < self.agreement_close_price:
                self.agreement_close_price = cd.low
        elif self.trade_action == Constants.ACTION_OPEN_SHORT:
            if self.agreement_close_price is None or cd.high > self.agreement_close_price:
                self.agreement_close_price = cd.high


    """
    平仓
    """
    def close_a_price(self, cd):
        if self.trade_action == Constants.ACTION_OPEN_LONG:
            if cd.low < self.close_price:
                return True
        elif self.trade_action == Constants.ACTION_OPEN_SHORT:
            if cd.high > self.close_price:
                return True
        return False

    """
    判断当前价是否超过止盈价位，如果超过就平仓
    """
    def close_a_price_by_ml_1_price(self, cd):
        if self.trade_action == Constants.ACTION_OPEN_LONG:
            if self.ml_1_price > cd.low:
                self.trade_action = Constants.ACTION_CLOSE_LONG
                # print(f"平仓 => {cd.datetime} 平仓价格 => {self.ml_1_price}")
                self.reset_ml_1_price()
                if self.sub_status == S3_Cons.SUB_STATUS_OF_ML_ONE:
                    self.reset_params_by_close_a_price()
        elif self.trade_action == Constants.ACTION_OPEN_SHORT:
            if self.ml_1_price < cd.high:
                # print(f"平仓 => {cd.datetime} 平仓价格 => {self.ml_1_price}")
                self.trade_action = Constants.ACTION_CLOSE_SHORT
                self.reset_ml_1_price()
                if self.sub_status == S3_Cons.SUB_STATUS_OF_ML_ONE:
                    self.reset_params_by_close_a_price()
    
        """
    判断当前价是否超过止盈价位，如果超过就平仓
    """
    def close_a_price_by_ml(self, cd):
        if self.trade_action == Constants.ACTION_OPEN_LONG:
            if self.ml > cd.low:
                self.trade_action = Constants.ACTION_CLOSE_LONG
                # print(f"平仓 => {cd.datetime} 平仓价格 => {self.ml_1_price}")
                if self.sub_status == S3_Cons.SUB_STATUS_OF_ML_ONE:
                    self.reset_params_by_close_a_price()
        elif self.trade_action == Constants.ACTION_OPEN_SHORT:
            if self.ml < cd.high:
                # print(f"平仓 => {cd.datetime} 平仓价格 => {self.ml_1_price}")
                self.trade_action = Constants.ACTION_CLOSE_SHORT
                if self.sub_status == S3_Cons.SUB_STATUS_OF_ML_ONE:
                    self.reset_params_by_close_a_price()
    
    """
    平仓之后重新设置参数
    """ 
    def reset_params_by_close_a_price(self):
        self.set_sub_status(S3_Cons.SUB_STATUS_OF_ML)

    """
    处理最大的幅度区间Rmax
    """    
    def handle_max_amplitude(self, cd):
        appear = False
        if self.max_l_to_d_interval.length >= self.max_r.length:
            if self.max_l_to_d_interval.length > self.max_amplitude.length:
                self.max_amplitude.direction = self.breakthrough_direction
                self.max_amplitude.start = self.max_l_to_d_interval.start_price            
                self.max_amplitude.end = self.max_l_to_d_interval.end_price
                self.max_amplitude.length = abs(self.max_amplitude.start - self.max_amplitude.end)
                self.max_amplitude.datetime = cd.datetime
                appear = True
                # print(f"相同方向设置最大的max_amplitude00000000000000000000000000000000000000 => {cd.datetime} => {self.max_amplitude} 方向 => {self.breakthrough_direction}")
        else:
            if self.max_r.length > self.max_amplitude.length:
                # 当r为最大的幅度时，改变方向
                self.reverse_direct()
                self.max_amplitude.direction = self.breakthrough_direction 
                self.max_amplitude.start = self.max_r.start_price
                self.max_amplitude.end = self.max_r.end_price
                self.max_amplitude.length = abs(self.max_amplitude.start - self.max_amplitude.end)
                self.max_amplitude.datetime = cd.datetime
                appear = True
                self.on_direction_change(cd)
                # print(f"不同方向设置最大的max_amplitudeooooooooooooooooooooooooooooooooooooooo => {cd.datetime} => {self.max_amplitude} 方向 => {self.breakthrough_direction}")
        if appear:
            # 重置R
            self.max_l_to_d_interval = None
            # 重置r
            self.max_r = None
        else:
            if Logic.is_exceed_max_amplitude_start_price(self.breakthrough_direction, self.max_amplitude, cd):
                self.reverse_direct_by_max_amplitude()
                self.on_direction_change(cd)
                print(f"突破max_amplitude的起始价格@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ => {cd.datetime}")
            elif Logic.is_exceed_max_amplitude_end_price(self.breakthrough_direction, self.max_amplitude, cd):
                self.set_direction_by_max_amplitude()
                self.on_direction_change(cd)
                
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
        # 重置h
        self.reset_h_price()
        self.h_price_max = None
        # 重置rrn
        self.rrn = None
    
    """
    趋势分析
    """
    def history_statistic_max_l_to_d(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            # 方向相同统计R
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd): 
                    if self.last_cd.high == self.last_cd.close and cd.open == cd.low and cd.open >= self.last_cd.close:
                        # 此处已经测试
                        max_l_to_d_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                        # print(f"此时跑到这里 {max_l_to_d_obj}")
                    else:  
                        max_l_to_d_obj = self.amplitude_obj(cd.low, cd.high)
                else:
                    if self.last_cd.close > self.last_cd.low and cd.open == cd.low and cd.open >= self.last_cd.close:
                        # max_l_to_d = abs(cd.high - self.last_cd.low)
                        max_l_to_d_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                    else:
                        max_l_to_d_obj = self.amplitude_obj(cd.low, cd.high)

            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close >= self.last_cd.low and cd.high >= cd.open and cd.open >= self.last_cd.close:
                        len = abs(cd.high - self.last_cd.low)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_l_to_d_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                        else:
                            max_l_to_d_obj = self.amplitude_obj(cd.low, cd.close)
                    else:
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_l_to_d_obj = self.amplitude_obj(cd.open, cd.high)
                        else:
                            max_l_to_d_obj = self.amplitude_obj(cd.low, cd.close)
                else:
                    if self.last_cd.high == self.last_cd.close and cd.high > cd.open and cd.open >= self.last_cd.close:
                        # 这里已经测试
                        max_l_to_d_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                    else:
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_l_to_d_obj = self.amplitude_obj(cd.open, cd.high)
                        else:
                            max_l_to_d_obj = self.amplitude_obj(cd.low, cd.close)
        else:
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close == self.last_cd.low and cd.open == cd.high and cd.open <= self.last_cd.close:
                        max_l_to_d_obj = self.amplitude_obj(self.last_cd.high, cd.low)
                    else:
                        max_l_to_d_obj = self.amplitude_obj(cd.high, cd.low)
                else:
                    if self.last_cd.close < self.last_cd.high and cd.open == cd.high and cd.open <= self.last_cd.close:
                        max_l_to_d_obj = self.amplitude_obj(self.last_cd.high, cd.low)
                    else:
                        max_l_to_d_obj = self.amplitude_obj(cd.high, cd.low)
            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close <= self.last_cd.high and cd.open >= cd.low and cd.open <= self.last_cd.close:
                        len = abs(self.last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = self.amplitude_obj(self.last_cd.high, cd.low)                                                    
                        else:
                            max_l_to_d_obj = self.amplitude_obj(cd.high, cd.close)
                    else:
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = self.amplitude_obj(cd.open, cd.low) 
                        else:
                            max_l_to_d_obj = self.amplitude_obj(cd.high, cd.close)
                else:
                    if self.last_cd.close == self.last_cd.low and cd.open > cd.low and self.last_cd.close >= cd.open:
                        len = abs(self.last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = self.amplitude_obj(self.last_cd.high, cd.low)
                        else:
                            max_l_to_d_obj = self.amplitude_obj(cd.high, cd.close)
                    else:
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = self.amplitude_obj(cd.open, cd.low) 
                        else:
                            max_l_to_d_obj = self.amplitude_obj(cd.high, cd.close) 


        # 判断是否出现极值d点
        if self.exceed_extremum_d(cd):
            # 设置点D
            self.set_extremum_d(cd)
            # 重置l数据
            self.reset_extremum_l() 
            # todo 重置h_price 参数
            self.reset_h_price()
        else:
            self.set_rrn(max_l_to_d_obj.length)
            # 设置extremum_l
            self.set_extremum_l(cd)
            # 设置h_price
            self.set_h_price(cd)

        # 记录下当前的max_l_to_d
        self.current_max_l_to_d_interval = max_l_to_d_obj
        # 记录最大的max_l_to_d
        self.set_max_l_to_d_interval_obj(max_l_to_d_obj)
        # 当子状态为L时就设置M_MAX_R 
        if self.sub_status == S3_Cons.SUB_STATUS_OF_TREND_COUNTER:
            self.set_M_MAX_R_obj(max_l_to_d_obj)

    """
    开始点设置R
    """ 
    def first_l_to_d(self, cd):
        obj = None
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.direction == Constants.DIRECTION_UP:
                obj = self.amplitude_obj(cd.low, cd.high)
            else:
                obj = self.amplitude_obj(cd.low, cd.close)
        else:
            if cd.direction == Constants.DIRECTION_UP:
                obj = self.amplitude_obj(cd.high, cd.close)
            else:
                obj = self.amplitude_obj(cd.high, cd.low)
        return obj

    """
    设置长度跟开始点价格、结束点价格
    """
    def amplitude_obj(self, start_price, end_price):
        obj = SimpleNamespace()
        obj.length = abs(start_price - end_price)
        obj.start_price = start_price
        obj.end_price = end_price
        return obj

    """
    分析统计最大的max_r
    """
    def history_statistic_max_r(self, cd): 
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if  self.last_cd.close <= self.last_cd.high and cd.open >= cd.low and self.last_cd.close >= cd.open:
                        len = abs(self.last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = self.amplitude_obj(self.last_cd.high, cd.low)
                        else:
                            max_r_obj = self.amplitude_obj(cd.high, cd.close)
                        max_len = max(abs(self.last_cd.high - cd.low), abs(cd.high - cd.close))
                    else:
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = self.amplitude_obj(cd.open, cd.low)
                        else:
                            max_r_obj = self.amplitude_obj(cd.high, cd.close)
                        max_len = max(abs(cd.open - cd.low), abs(cd.high - cd.close))
                else:
                    if self.last_cd.close == self.last_cd.low and cd.open > cd.low and self.last_cd.close >= cd.open:
                        max_len = max(abs(self.last_cd.high - cd.low), abs(cd.high - cd.close))
                        len = abs(self.last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = self.amplitude_obj(self.last_cd.high, cd.low)
                        else:
                            max_r_obj = self.amplitude_obj(cd.high, cd.close)
                    else:
                        max_len = max(abs(cd.open - cd.low), abs(cd.high - cd.close))
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = self.amplitude_obj(cd.open, cd.low)
                        else:
                            max_r_obj = self.amplitude_obj(cd.high, cd.close)
            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close == self.last_cd.low and cd.open == cd.high and self.last_cd.close >= cd.open:
                        # 已经测试
                        max_len = abs(self.last_cd.high - cd.low)
                        max_r_obj = self.amplitude_obj(self.last_cd.high, cd.low)
                    else:
                        max_len = Logic.max_amplitude_length(cd)
                        max_r_obj = self.amplitude_obj(cd.high, cd.low)
                else:
                    if self.last_cd.high > self.last_cd.close and cd.open == cd.high and self.last_cd.close >= cd.open:
                        max_len = abs(self.last_cd.high - cd.low)
                        max_r_obj = self.amplitude_obj(self.last_cd.high, cd.low)
                    else:
                        # 已经测试
                        max_len = Logic.max_amplitude_length(cd)
                        max_r_obj = self.amplitude_obj(cd.high, cd.low)
        else:
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close >= self.last_cd.low and cd.open <= cd.high and cd.open >= self.last_cd.close:
                        max_len = abs(cd.high - self.last_cd.low)
                        max_r_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                    else:
                        max_len = max(abs(cd.high - cd.open), abs(cd.close - cd.low))
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_r_obj = self.amplitude_obj(cd.open, cd.high)
                        else:
                            max_r_obj = self.amplitude_obj(cd.low, cd.close)
                else:
                    if self.last_cd.close == self.last_cd.high and cd.open < cd.high and cd.open >= self.last_cd.close:
                        max_len = max(abs(cd.high - self.last_cd.low), abs(cd.close - cd.low)) 
                        len = abs(cd.high - self.last_cd.low)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_r_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                        else:
                            max_r_obj = self.amplitude_obj(cd.low, cd.close)
                    else:
                        max_len = max(abs(cd.high - cd.open), abs(cd.close - cd.low))
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_r_obj = self.amplitude_obj(cd.open, cd.high)
                        else:
                            max_r_obj = self.amplitude_obj(cd.low, cd.close)
            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close == self.last_cd.high and cd.open == cd.high and cd.open >= self.last_cd.close:
                        max_len = abs(cd.high - self.last_cd.low)
                        max_r_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                    else:
                        # 已测试
                        max_len = Logic.max_amplitude_length(cd)
                        max_r_obj = self.amplitude_obj(cd.low, cd.high)
                else:
                    if self.last_cd.close > self.last_cd.low and cd.open == cd.high and cd.open >= self.last_cd.close:
                        max_len = abs(cd.high - self.last_cd.low)
                        max_r_obj = self.amplitude_obj(self.last_cd.low, cd.high)
                    else:
                        max_len = Logic.max_amplitude_length(cd)
                        max_r_obj = self.amplitude_obj(cd.low, cd.high)
        if max_len != max_r_obj.length: 
            print(f"max_r对象 => {self.max_r}")
            print(f"出现了异常，要检查,datetime:{cd.datetime} max_len:{max_len} max_r_obj.length => {max_r_obj.length}")
        self.set_max_r(max_r_obj) 
                # 当子状态为L时就设置M_MAX_R 
        if self.sub_status == S3_Cons.SUB_STATUS_OF_TREND_COUNTER:
            self.set_m_max_r(max_r_obj)   

    """
    设置走势方向
    设置最大的幅度，包括开始价、结束价，幅度值
    """
    def init_set_max_amplitude(self, cd):
        # 当前点的方向决定走势方向
        self.breakthrough_direction = cd.direction
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
        self.max_amplitude = current

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
    处于逆趋势中
    """

    def in_a_counter_trend(self):
        if self.counter_trend_status == Constants.STATUS_COUNTER_TREND_YES:
            return True
        else:
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
        elif self.max_amplitude.direction == Constants.DIRECTION_DOWN:
            self.breakthrough_direction = Constants.DIRECTION_UP

    """
    通过max_amplitude制定方向
    """
    def set_direction_by_max_amplitude(self):
        self.breakthrough_direction = self.max_amplitude.direction

    """
    没有试错机会重新开始
    """

    def restart(self):
        self.reference_point_d = None  # 振荡的参考点D
        self.extremum_d_price = None  # 设置极值d_price为None
        self.breakthrough_direction = None  # 突破的方向 -1 向下 1 向上
        self.max_l_to_d_interval = None  # 最大上涨的间隔
        self.current_status = Constants.STATUS_NONE  # 当前状态
        self.counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态
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
        if Logic.is_realtime_start_minute(cd.datetime):
            return
        if self.history_status == Constants.HISTORY_STATUS_OF_NONE: 
            self.histoty_status_none(cd)
        elif self.history_status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
            self.statistic(cd)
        # 判断是否需要合并,当当前分钟为直线时考虑
        self.last_cd = Logic.handle_last_cd(self.last_cd, cd)
    
    """
    实时分析    
    """
    def realtime_analysis1(self, cd):
        # if Logic.is_start_minute(cd.datetime):
        #     return
        if self.history_status == Constants.HISTORY_STATUS_OF_NONE: 
            self.histoty_status_none(cd)
        elif self.history_status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
            self.statistic(cd)
        # 判断是否需要合并,当当前分钟为直线时考虑
        self.last_cd = Logic.handle_last_cd(self.last_cd, cd)

    """
    历史行情数据分析
    """
    def analysis(self, vt_symbol, frequent=1):
        try:
           data_file = open(Constants.STRATEGIES_DATA_PATH + f"{vt_symbol}_{frequent}m.csv", 'r')
        except Exception as e:
            print(f"无法打开{vt_symbol}_{frequent}m.csv文件", e)
            data_file.close()
            os._exit(0)
        while True:
            line = data_file.readline()
            if not line:
                break

            temp_array = line.split(',')
            if len(temp_array) > 0:
                try:
                    cd = Logic.history_price_to_data_object(temp_array, line)  # 当前时间单位的相关数据
                except Exception as e:
                    continue
                if self.history_status == Constants.HISTORY_STATUS_OF_NONE: 
                    self.histoty_status_none(cd)
                elif self.history_status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
                    self.statistic(cd)
            # 判断是否需要合并,当当前分钟为直线时考虑
            self.last_cd = Logic.handle_last_cd(self.last_cd, cd)
        data_file.close()
