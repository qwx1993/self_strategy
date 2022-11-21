"""
"""
import os
import sys
from logic import Logic
from tick_logic import TickLogic
from constants import Constants


class Tick:
    breakthrough_direction = None  # 突破的方向 -1 开空 1 开多
    sub_status = None  # 非加速振荡子状态
    direction_type = None  # 走势方向，以顺趋势为参考
    first_line_list = []
    d_to_l = []  # d到l元素记录
    l_to_d = [] # l到d元素记录

    max_l_to_d_interval = None  # 最大上涨的间隔,即R
    max_l_to_d_k = None # 最大上涨的幅度的斜率
    max_r = None  # 表示从dn-ln的最大值，d1点开始
    max_r_k = None

    current_status = Constants.STATUS_NONE  # 当前状态，目前就无状态跟非加速振荡

    counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态，默认非逆趋势状态

    extremum_d = None  # 极值点D
    extremum_l = None # 极值点L
    h_price = None # 仅次于D点价格的极值
    rrn = None  # 逆趋势止盈使用的参数
    open_price = None # 开仓价
    """
    初始化
    """

    def __init__(self):
        # 所有的list数据需要初始化
        self.d_to_l = []  # d到l元素记录
        self.l_to_d = []  # l到d元素记录
        self.first_line_list = [] # 刚开始的位置

    """
    当前状态为STATUS_NONE时的逻辑
    """

    def status_none(self, cd):
        self.first_line(cd)

    """
    振荡区间处理
    参考点A不存在就设置当前点为参考点A,A.open为振荡区间的参考价格
    存在参考点A就判断当前点cd是否超出了振荡区间范围，超出就检测是否满足：出现次数最多的最高点B1和最低点B2形成振荡区间，至少3次以上（通过画直线辅佐）
    满足振荡条件时就判断是否满足突破条件【cd.high - cd.low > 5 * b1_to_b2_interval】
    一旦突破就设置突破方向、参考点D、b1_price、最大下降幅度、最大上涨幅度、情况一止损点
    设置状态为非加速振荡状态，非加速振荡子状态为寻找D2
    """

    def first_line(self, cd):
        # 设置最后上涨或下跌趋势的list
        self.first_line_list.append(cd)
        if len(self.first_line_list) >= 2:
            first_price = self.first_line_list[0].current
            last_price = self.first_line_list[-1].current
            if first_price > last_price:
                self.breakthrough_direction = Constants.DIRECTION_DOWN
            elif first_price < last_price:
                self.breakthrough_direction = Constants.DIRECTION_UP
            else:
                self.breakthrough_direction == Constants.DIRECTION_NONE
            if not self.breakthrough_direction == Constants.DIRECTION_NONE:
                # 设置寻找D点状态
                self.set_status(Constants.STATUS_FIND_D1)   

    """
    突破寻找D点
    """
    def find_d(self, cd):
        # 如果改变了方向，即出现了D点
        if TickLogic.keep_direction(cd, self.first_line_list):
            self.first_line_list.append(cd)
        else:
            last_cd = self.first_line_list[-1]
            # 设置极限Dn
            self.set_extremum_d(last_cd)

            # 设置最大的上涨幅度
            self.max_l_to_d_interval = None
            self.set_max_l_to_d_interval_data(self.first_line_list)

            # 设置为非加速振荡状态
            self.set_status(Constants.NON_ACCELERATING_OSCILLATION)
            # 设置子状态为
            self.set_sub_status(Constants.SUB_STATUS_OF_L1)
            # 设置方向类型
            self.direction_type = Constants.DIRECTION_TYPE_OF_D_TO_L
            # 设置d到l的数据
            self.d_to_l = [last_cd, cd]
            print(f"d_to_l```` => {self.d_to_l}")
            # 直接进入非加速振荡判断
            # self.non_accelerating_oscillation_for_s1(cd)

    """\
    非振荡加速
    """

    def non_accelerating_oscillation(self, cd):
        # 判断是否为非加速振荡的逆趋势阶段
        self.statistic(cd)


    """
    统计d跟l
    """
    def statistic(self, cd):
        if self.direction_type == Constants.DIRECTION_TYPE_OF_D_TO_L:
            keep_direction = TickLogic.keep_direction(cd, self.d_to_l)
            if keep_direction:
                self.d_to_l.append(cd)
                # 逆趋势逻辑判断
                if TickLogic.is_counter_trend(self.d_to_l, self.max_l_to_d_interval, self.max_l_to_d_k):
                    # todo 需要讨论逆趋势的内容
                    print(f"出现逆趋势 => {cd.datetime}")
                    self.counter_trend_logic(cd)
            else:
                # 刷新最大下降幅度
                self.set_max_r(self.d_to_l)
                # 重置l_tp_d
                last_d_to_l_cd = self.d_to_l[-1]
                self.l_to_d = [last_d_to_l_cd, cd]
                self.direction_type = Constants.DIRECTION_TYPE_OF_L_TO_D
                # 出现l就设置l
                self.set_extremum_l(last_d_to_l_cd)
        elif self.direction_type == Constants.DIRECTION_TYPE_OF_L_TO_D:
            keep_direction = TickLogic.keep_direction(cd, self.l_to_d)
            if keep_direction:
                self.l_to_d.append(cd)
            else:
                self.set_max_l_to_d_interval_data(self.l_to_d)
                last_l_to_d = self.l_to_d[-1]
                self.d_to_l = [last_l_to_d, cd]
                self.direction_type = Constants.DIRECTION_TYPE_OF_D_TO_L
                # 判断是否极值
                if self.exceed_extremum_d(last_l_to_d):
                    # 重置极限值d
                    self.set_extremum_d(last_l_to_d)
                else:
                    self.set_rrn(self.l_to_d)
                    # 设置h_price
                    self.set_h_price(last_l_to_d)
                    if TickLogic.can_open_a_price(self.h_price, self.counter_trend_status):
                        self.set_status(Constants.TICK_STATUS_PAUSE)   
                        self.open_price = last_l_to_d.current

    # 逆趋势逻辑
    def counter_trend_logic(self, cd):
        # 改变方向
        self.reverse_direct()   
        # 设置状态为FIND_D
        self.set_status(Constants.STATUS_FIND_D1)
        self.first_line_list = self.d_to_l
        # 重置R
        self.max_l_to_d_interval = None
        self.max_l_to_d_k = None
        # 重置r
        self.max_r = None
        self.max_r_k = None
        # 重置h
        self.h_price = None
        # 设置出现了逆趋势
        self.counter_trend_status = Constants.STATUS_COUNTER_TREND_YES       



    """
    设置最大的dn_to_ln
    当dn_to_ln_max的值为None的时候，设置为极致点D对应数值
    """

    def set_max_r(self, ls):
        first_current = ls[0].current
        last_current = ls[-1].current
        current_r = abs(first_current - last_current)
        if self.max_r is None or self.max_r < current_r:
            self.max_r = current_r
            first_cd_time = ls[0].datetime
            last_cd_time = ls[-1].datetime
            # 时间差计算
            diff_seconds = TickLogic.diff_seconds(last_cd_time, first_cd_time)
            if diff_seconds == 0:
                diff_seconds = 1
            self.max_r_k = current_r/diff_seconds
    
        """
    重置当前状态以及与状态相关的所有变量
    """

    def reset_status(self):
        self.current_status = Constants.STATUS_NONE

    """
    将当前状态设置成某状态
    """

    def set_status(self, status):
        self.current_status = status

    """
    设置当前是否为逆趋势中， 包括两种状态，逆趋势状态、非逆趋势状态
    """

    def set_counter_trend_status(self, status):
        self.counter_trend_status = status

    """
    设置非加速振荡子状态
    """

    def set_sub_status(self, status):
        self.sub_status = status

    """
    设置最大的l_to_d间隔数据，以及斜率
    """

    def set_max_l_to_d_interval_data(self, ls):
        first_cd = ls[0]
        last_cd = ls[-1]

        current_l_to_d_interval = abs(last_cd.current - first_cd.current)
        if (self.max_l_to_d_interval is None) or (current_l_to_d_interval > self.max_l_to_d_interval):
            self.max_l_to_d_interval = current_l_to_d_interval
            self.max_l_to_d_k = self.max_l_to_d_interval/TickLogic.diff_seconds(last_cd.datetime, first_cd.datetime)

    """
    rrn 表示的是寻找Dn过程中，出现比Dn小的Hn过程的最大值
    """
    def set_rrn(self, ls):
        first_current = ls[0].current
        last_current = ls[-1].current
        current_rrn = abs(first_current - last_current)
        if self.rrn is None or current_rrn > self.rrn:
            self.rrn = current_rrn

    """
    设置极值点D
    当开多的时候，大于之前的current就更新为当前值
    当开空的时候，小于之前的current就更新为当前值
    """
    def set_extremum_d(self, dn):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if (self.extremum_d is None) or dn.current > self.extremum_d.current:
                self.extremum_d = dn
        else:
            if (self.extremum_d is None) or dn.current < self.extremum_d.current:
                self.extremum_d = dn
    
    """
    设置极值点l
    当开多的时候，小于之前的current就更新为当前值
    当开空的时候，大于之前的current就更新为当前值
    """
    def set_extremum_l(self, ln):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if (self.extremum_l is None) or ln.current < self.extremum_l.current:
                self.extremum_l = ln
        else:
            if (self.extremum_l is None) or ln.current > self.extremum_l.current:
                self.extremum_l = ln

    """
    设置仅次于d点价格的极值h
    """
    def set_h_price(self, hn):
        current_price = hn.current
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if current_price < self.extremum_d.current:
                if (self.h_price is None) or current_price > self.h_price:
                    self.h_price = current_price
        else:
            if current_price > self.extremum_d.current:
                if (self.h_price is None) or current_price < self.h_price:
                    self.h_price = current_price

    """
    是否出现极值
    """

    def exceed_extremum_d(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.current > self.extremum_d.current:
                return True
            else:
                return False
        else:
            if cd.current < self.extremum_d.current:
                return True
            else:
                return False

    """
    是否出现极值L
    """
    def exceed_extremum_l(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_DOWN:
            if cd.current < self.extremum_l.current:
                return True
            else:
                return False
        else:
            if cd.current > self.extremum_l.current:
                return True
            else:
                return False

    """
    处于逆趋势中
    """
    # def in_a_counter_trend(self):
    #     if self.counter_trend_status == Constants.STATUS_COUNTER_TREND_YES:
    #         return True
    #     else:
    #         return False

    """
    初始化逆趋势
    """

    # def init_counter_trend(self, cd):
    #     # 改变突破方向
    #     self.reverse_direct()
    #     # 改变方向类型
    #     self.reverse_direction_type()
    #     # 设置参考点d
    #     self.set_counter_trend_status(Constants.STATUS_COUNTER_TREND_YES)
    #     self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_YES
    #     # 重置振荡的参数
    #     self.oscillating_interval_list = []
    #     self.price_dict = {}
    #     self.max_r = None
    #     self.max_r_k = None
    #     self.reference_point_d = None

    """
    逆趋势设置r的初始值
    逆开空情况下
    """

    # def counter_trend_reset_r(self, cd):
    #     if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
    #         self.max_r = abs(cd.high - cd.close)
    #     else:
    #         self.max_r = abs(cd.low - cd.close)

    """
    改变方向
    """
    def reverse_direct(self):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            self.breakthrough_direction = Constants.DIRECTION_DOWN
        elif self.breakthrough_direction == Constants.DIRECTION_DOWN:
            self.breakthrough_direction = Constants.DIRECTION_UP

    """
    逆趋势出现时改变方向
    """
    def reverse_direction_type(self):
        if self.direction_type == Constants.DIRECTION_TYPE_OF_D_TO_L:
            self.direction_type = Constants.DIRECTION_TYPE_OF_L_TO_D
            self.l_to_d = self.d_to_l
        else:
            self.direction_type = Constants.DIRECTION_TYPE_OF_D_TO_L
            self.d_to_l = self.l_to_d

    """
    没有试错机会重新开始
    """

    def restart(self):
        breakthrough_direction = None  # 突破的方向 -1 开空 1 开多
        sub_status = None  # 非加速振荡子状态
        direction_type = None  # 走势方向，以顺趋势为参考
        first_line_list = []
        d_to_l = []  # d到l元素记录
        l_to_d = [] # l到d元素记录

        max_l_to_d_interval = None  # 最大上涨的间隔,即R
        max_l_to_d_k = None # 最大上涨的幅度的斜率
        max_r = None  # 表示从dn-ln的最大值，d1点开始
        max_r_k = None

        current_status = Constants.STATUS_NONE  # 当前状态，目前就无状态跟非加速振荡

        counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态，默认非逆趋势状态

        extremum_d = None  # 极值点D
        extremum_l = None # 极值点L
        h_price = None # 仅次于D点价格的极值
        rrn = None  # 逆趋势止盈使用的参数

    """
    一行行地读取文件数据并且分析
    """

    def analysis(self, cd):
        if self.current_status == Constants.STATUS_NONE:
            self.status_none(cd)
        elif self.current_status == Constants.STATUS_FIND_D1:
            self.find_d(cd)
        elif self.current_status == Constants.NON_ACCELERATING_OSCILLATION:
            self.non_accelerating_oscillation(cd)
