"""
main.py
读取data文件夹中的所有csv文件，针对每个文件计算出该交易策略的胜率和赚钱点数
"""
import os
import sys
from self_strategy.constants import Constants
from self_strategy.logic import Logic
from types import SimpleNamespace
# 
class History:
    reference_point_d = None  # 振荡的参考点D
    breakthrough_direction = None # 突破的方向 -1 开空 1开多
    non_accelerating_oscillation_sub_status = None  # 非加速振荡子状态

    # 情况一的参数
    stop_loss_ln_price = None  # 情况一的止损点价位，出现新的dn才重置
    s1_status = None  # 情况一的状态
    ln_price = None  # 用作情况二的止损价格, 止损点为ln - 1

    max_l_to_d_interval = None  # 最大上涨的间隔,即R
    max_r = None  # 表示从dn-ln的最大值，d1点开始
    rrn = None  # 逆趋势止盈使用的参数  todo 暂时不使用

    current_status = Constants.STATUS_NONE  # 当前状态，目前就无状态跟非加速振荡

    counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态，默认非逆趋势状态
    need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_NO  # 默认不需要检测逆趋势

    actions = []  # 记录所有的动作，包括开空，开多，逆开空，逆开多，注意：逆趋势下是两倍仓位
    s1_actions = []  # 记录所有的情况一动作
    s2_actions = []  # 记录所有的情况二动作
    lines_written_to_temp = 0  # 写入临时文件的行数
    has_current_line_written = False  # 当前分钟的数据行是否写到了供画图用的临时文件中
    data_file = None  # 正在分析的数据文件
    stop_surplus_price = 0  # 设置止盈价
    need_day_close = False  # 是否需要平仓、True需要、False不需要
    s1_need_day_close = False
    s2_need_day_close = False
    extremum_d_price = None  # 极致d的price
    extremum_d = None  # 极值点D
    extremum_l_price = None # 极值点l的price
    extremum_l = None # 极值点l

    h_price = None # h点，表示比仅次于d点第二高点

    s2_status = None  # 情况二的状态
    s1_action_record = None  # 交易动作记录
    counter_trend_action_record = None

    history_status = Constants.HISTORY_STATUS_OF_NONE # 历史状态
    last_cd = None # 上一点
    max_amplitude = None # 最大幅度对象
    h_price_max = None # h的极值
    trade_action = None

    """
    初始化
    """

    # def __init__(self):
    #     # 所有的list数据需要初始化
    #     print(f"初始化")

    """
    添加对应的动作，目前包括开空、平空、开多、平多、逆开空、逆平空、逆开多、逆平多
    逆开空、逆平空、逆开多、逆平多 时为2倍仓位
    """

    def add_action(self, cd, action, price, actions_index=Constants.ACTIONS_INDEX_DEFAULT):
        record = {
            "price": price,
            "action": action,
            "datetime": cd.datetime
        }

        # 写交易记录
        if actions_index == Constants.ACTIONS_INDEX_DEFAULT:
            self.counter_trend_action_record = record
            self.actions.append(record)
        elif actions_index == Constants.ACTIONS_INDEX_ONE:
            self.s1_action_record = record
            self.s1_actions.append(record)
        return record

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

    def set_non_accelerating_oscillation_sub_status(self, status):
        self.non_accelerating_oscillation_sub_status = status

    """
    设置情况一的状态
    """

    def set_s1_status(self, status):
        self.s1_status = status

    """
    设置情况二的状态
    """

    def set_s2_status(self, status):
        self.s2_status = status

    """
    设置新的止损点
    只有出现新的Dn才重新设置
    """

    def set_stop_loss_ln(self, cd):
        if self.stop_loss_ln_price is None:
            self.stop_loss_ln_price = cd.close
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if cd.low > self.stop_loss_ln_price:
                self.stop_loss_ln_price = cd.low
        else:
            if cd.high < self.stop_loss_ln_price:
                self.stop_loss_ln_price = cd.high

    """
    设置最大的l_to_d间隔数据
    """

    def set_max_l_to_d_interval_obj(self, obj):
        if (self.max_l_to_d_interval is None) or (obj.length > self.max_l_to_d_interval.length):
            self.max_l_to_d_interval = obj

    """
    设置情况二所需的最大l_to_h
    """

    def set_situation2_max_l_to_h(self, cd):
        current_l_to_h = abs(cd.high - cd.low)
        if (self.situation2_max_l_to_h is None) or (current_l_to_h > self.situation2_max_l_to_h):
            self.situation2_max_l_to_h = current_l_to_h

    """
    rrn 表示的是寻找Dn过程中，出现比Dn小的Hn过程的最大值
    """
    def set_rrn(self, current_rrn):
       if self.rrn is None or current_rrn > self.rrn:
        self.rrn = current_rrn 

    """
    设置情况二开仓需要的ln_price
    """

    def set_ln_price(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if (self.ln_price is None) or cd.low < self.ln_price:
                self.ln_price = cd.low
        else:
            if (self.ln_price is None) or cd.high > self.ln_price:
                self.ln_price = cd.high

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
        if self.extremum_d_price is not None and Logic.is_low_point(self.breakthrough_direction, self.last_cd, ln):
            if self.breakthrough_direction == Constants.DIRECTION_UP:
                if (self.extremum_l_price is None) or ln.low < self.extremum_l_price:
                    self.extremum_l_price = ln.low
                    self.extremum_l = ln
            else:
                if (self.extremum_l_price is None) or ln.high > self.extremum_l_price:
                    self.extremum_l_price = ln.high
                    self.extremum_l = ln
    
    """
    重置extremum_l的值
    """
    def reset_extremum_l(self):
        self.extremum_l = None
        self.extremum_l_price = None
    
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
    重置h_price参数
    """     
    def reset_h_price(self):
        self.h_price = None

    """
    将当前行的数据前面加上行数，后面加上状态/动作，写入临时文件
    :param temp_file 临时文件
    :param line_content 行内容
    :param annotation_index 注释索引
    :param open_price 开多或者开空价格
    :param stop_price 平空或者平多价格
    :param b1_price b1参考线的y坐标
    :param b1_offset b1参考线的长度偏移2⃣量
    """

    def write_to_temp(self, temp_file, line_content, annotation_index, open_price=0, stop_price=0, b1_price=0,
                      b1_offset=0, note=""):
        return
        temp_file.write(line_content.rstrip() + "," + str(annotation_index) + "," + str(self.lines_written_to_temp) +
                        "," + Constants.STR_ACTIONS_AND_STATES[annotation_index]["en"] + "," + str(open_price) + "," +
                        str(stop_price) + "," + str(b1_price) + "," +
                        str(b1_offset) + "," + note + "\n")
        self.lines_written_to_temp += 1
        self.has_current_line_written = True

    """
    平仓及其相关操作
    写入一个平空或平多或逆趋势平空或逆趋势平多动作
    重置所有属性参数，下个开盘日重新开始
    :param cd: 当前时间单位的价格信息
    :param temp_file: 供画图用的临时csv文件
    :param line: 从正在分析的csv文件中读取出来的当前行的原始字符串
    :param action: 当前动作，可能为ACTION_CLOSE_SHORT或者ACTION_CLOSE_LONG
    :param annotation: 在画图时需要显示的标识字符串
    """

    def close_future(self, cd, temp_file, line, annotation, actions_index):
        self.action_close_long_or_short(cd, cd.close, actions_index)
        self.write_to_temp(temp_file, line, annotation, 0, cd.close)

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

    
    def handle_max_amplitude(self, cd):
        appear = False
        if self.max_l_to_d_interval.length >= self.max_r.length:
            if self.max_l_to_d_interval.length > self.max_amplitude.length:
                self.max_amplitude.direction = self.breakthrough_direction
                self.max_amplitude.start = self.max_l_to_d_interval.start_price            
                self.max_amplitude.end = self.max_l_to_d_interval.end_price
                self.max_amplitude.length = abs(self.max_amplitude.start - self.max_amplitude.end)
                appear = True
                print(f"相同方向设置最大的max_amplitude => {cd.datetime} => {self.max_amplitude}")
        else:
            if self.max_r.length > self.max_amplitude.length:
                # 当r为最大的幅度时，改变方向
                self.reverse_direct()
                self.max_amplitude.direction = self.breakthrough_direction 
                self.max_amplitude.start = self.max_r.start_price
                self.max_amplitude.end = self.max_r.end_price
                self.max_amplitude.length = abs(self.max_amplitude.start - self.max_amplitude.end)
                appear = True
                self.on_direction_change(cd)
                print(f"不同方向设置最大的max_amplitude => {cd.datetime} => {self.max_amplitude}")
        if appear:
            # 重置R
            self.max_l_to_d_interval = None
            # 重置r
            self.max_r = None
        else:
            if Logic.is_exceed_max_amplitude_start_price(cd):
                self.reverse_direct_by_max_amplitude()
                print(f"突破max_amplitude的起始价格@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ => {cd.datetime}")
            elif Logic.is_exceed_max_amplitude_end_price(self.breakthrough_direction, self.max_amplitude, cd):
                self.set_direction_by_max_amplitude()

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
                    if self.last_cd.close > self.last_cd.low and cd.high > cd.open and cd.open >= self.last_cd.close:
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
                    if self.last_cd.close < self.last_cd.high and cd.open > cd.low and cd.open <= self.last_cd.close:
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

        self.set_max_l_to_d_interval_obj(max_l_to_d_obj)

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
                    if  self.last_cd.close < self.last_cd.high and cd.open > cd.low and self.last_cd.close >= cd.open:
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
                    if self.last_cd.close > self.last_cd.low and cd.open < cd.high and cd.open >= self.last_cd.close:
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
    获取情况二的止损价，以止损点对应价位为止损价
    """

    def get_situation2_stop_loss_price(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            return min(self.stop_loss_ln_price, cd.high)
        else:
            return max(self.stop_loss_ln_price, cd.low)

    """
    情况二开盘价
    """

    def situation2_open_a_position_price(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            return cd.low + self.situation2_max_l_to_h
        else:
            return cd.high - self.situation2_max_l_to_h

    """
    开空或者开多动作
    振荡向上时开多
    振荡向下时开空
    """

    def action_open_long_or_short(self, cd, price, actions_index):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if self.in_a_counter_trend():
                self.add_action(cd, Constants.ACTION_REVERSE_OPEN_LONG, price, actions_index)
            else:
                self.add_action(cd, Constants.ACTION_OPEN_LONG, price, actions_index)
        else:
            if self.in_a_counter_trend():
                self.add_action(cd, Constants.ACTION_REVERSE_OPEN_SHORT, price, actions_index)
            else:
                self.add_action(cd, Constants.ACTION_OPEN_SHORT, price, actions_index)

    """
    平空或者平多动作
    振荡向上时平多
    振荡向下时平空
    """

    def action_close_long_or_short(self, cd, price, actions_index):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            if self.in_a_counter_trend():
                self.add_action(cd, Constants.ACTION_REVERSE_CLOSE_LONG, price, actions_index)
            else:
                self.add_action(cd, Constants.ACTION_CLOSE_LONG, price, actions_index)
        else:
            if self.in_a_counter_trend():
                self.add_action(cd, Constants.ACTION_REVERSE_CLOSE_SHORT, price, actions_index)
            else:
                # todo 后面删除
                if actions_index == Constants.ACTIONS_INDEX_DEFAULT:
                    if self.actions[-1]['action'] != Constants.ACTION_OPEN_SHORT:
                        print(f"问题点逆 => {cd} {self.s1_actions}")
                elif actions_index == Constants.ACTIONS_INDEX_ONE:
                    if self.s1_actions[-1]['action'] != Constants.ACTION_OPEN_SHORT:
                        print(f"问题点1 => {cd} {self.s1_actions}")
                elif actions_index == Constants.ACTIONS_INDEX_TWO:
                    if self.s2_actions[-1]['action'] != Constants.ACTION_OPEN_SHORT:
                        print(f"问题点2 => {cd} {self.s2_actions}")

                self.add_action(cd, Constants.ACTION_CLOSE_SHORT, price, actions_index)

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
    初始化逆趋势
    """

    def init_counter_trend(self, cd):
        # 改变突破方向
        self.reverse_direct()
        # todo 设置ln为b1_price 这里要修改
        self.b1_price = self.lowest_point_l.close
        # 设置参考点d
        self.reference_point_d = cd
        # 设置最低点
        self.lowest_point_l = None
        self.set_lowest_point_l(cd)
        # # 设置ln_price
        # self.stop_loss_ln_price = cd.close
        # self.set_non_accelerating_oscillation_sub_status(
        #     Constants.SUB_STATUS_OF_D2)
        # 设置为逆趋势中, 逆趋势中需要检测振荡
        self.set_counter_trend_status(Constants.STATUS_COUNTER_TREND_YES)
        self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_YES
        # 重置振荡的参数
        self.oscillating_interval_list = []
        # 设置小r方向
        self.counter_trend_reset_r(cd)

    """
    逆趋势设置r的初始值
    逆开空情况下
    """

    def counter_trend_reset_r(self, cd):
        if self.breakthrough_direction == Constants.DIRECTION_UP:
            self.max_r = abs(cd.high - cd.close)
        else:
            self.max_r = abs(cd.low - cd.close)

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
    试错重新设置值
    """

    def refresh_start_data(self, cd):
        # 设置最大的下降幅度
        self.lowest_point_l = None
        # 设置最低点
        # 设置ln_price
        self.stop_loss_ln_price = cd.close
        self.reference_point_d = cd
        # 设置极值d的价格
        self.extremum_d_price = None
        self.set_extremum_d(cd)
        # 设置情况二判定的ln_price
        self.ln_price = None
        self.situation2_max_l_to_h = None
        # 设置为寻找D2状态
        self.set_non_accelerating_oscillation_sub_status(
            Constants.SUB_STATUS_OF_D2)
        if self.s1_status == Constants.SITUATION_ONE_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH:
            self.set_s1_status(Constants.SITUATION_ONE_STATUS_OF_D2)
        # todo 这里要改的
        if self.s2_status == Constants.SITUATION_TWO_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH:
            self.set_s2_status(Constants.SITUATION_TWO_STATUS_OF_D2)

    """
    当天收盘前的最后一分钟，如果有仓要强行平仓，因为目前的策略不做日间交易
    """

    def last_minute_of_the_day(self, cd, temp_file, line):
        if self.need_day_close:
            self.close_future(cd, temp_file, line, Constants.INDEX_DAY_CLOSE, Constants.ACTIONS_INDEX_DEFAULT)
            # 设置需要检测日结束平仓为False
            self.need_day_close = False
        if self.s1_need_day_close:
            self.close_future(cd, temp_file, line, Constants.INDEX_DAY_CLOSE, Constants.ACTIONS_INDEX_ONE)
            self.s1_need_day_close = False
        if self.s2_need_day_close:
            self.close_future(cd, temp_file, line, Constants.INDEX_DAY_CLOSE, Constants.ACTIONS_INDEX_TWO)
            self.s2_need_day_close = False
        self.restart()
        # 重新开始振荡数统计
        self.last_oscillation_number = 0
        # 最后将一天的汇总到actions里面
        # print(self.actions)
        self.actions = self.actions + self.s1_actions + self.s2_actions
        self.s1_actions = []
        self.s2_actions = []

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
        if Logic.is_start_minute(cd.datetime):
            return
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
                
                self.last_cd = cd
        data_file.close()
