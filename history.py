"""
main.py
读取data文件夹中的所有csv文件，针对每个文件计算出该交易策略的胜率和赚钱点数
"""
import os
import sys
from tkinter import E
from tkinter.messagebox import NO
from self_strategy.constants import Constants
from self_strategy.logic import Logic

class Analysis:
    reference_point_d = None  # 振荡的参考点D
    b1_to_b2_interval = None  # 振荡区间的最大值跟最小值的距离
    b_list = []  # b1的close值
    breakthrough_direction = None  # 突破的方向 -1 开空 1 开多
    non_accelerating_oscillation_sub_status = None  # 非加速振荡子状态

    # 情况一的参数
    stop_loss_ln_price = None  # 情况一的止损点价位，出现新的dn才重置
    s1_status = None  # 情况一的状态
    ln_price = None  # 用作情况二的止损价格, 止损点为ln - 1
    b1_price = None  # b1点的价位

    lowest_point_l = None  # l的最地点

    max_l_to_d_interval = None  # 最大上涨的间隔,即R
    max_r = None  # 表示从dn-ln的最大值，d1点开始

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
    situation2_max_l_to_h = None  # 用作情况二的上升幅度 [对应文档中的rrn]
    last_oscillation_number = 0  # 前面振荡的次数

    s2_status = None  # 情况二的状态

    rrn = None  # 逆趋势止盈使用的参数  todo 暂时不使用

    s1_action_record = None  # 交易动作记录
    counter_trend_action_record = None
    test_count = 1

    history_status = None # 历史状态
    last_cd = None # 上一点


    """
    初始化
    """

    def __init__(self):
        # 所有的list数据需要初始化
        self.oscillating_interval_list = []
        self.b_list = []


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
    重置A点，振荡区间、b1tob2间隔
    """

    def reset_reference_point_a(self):
        self.oscillating_interval_list = []
        self.b1_to_b2_interval = None

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
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            if cd.low > self.stop_loss_ln_price:
                self.stop_loss_ln_price = cd.low
        else:
            if cd.high < self.stop_loss_ln_price:
                self.stop_loss_ln_price = cd.high

    """
    设置最大的l_to_d间隔数据
    """

    def set_max_l_to_d_interval_data(self, len):
        if (self.max_l_to_d_interval is None) or (len > self.max_l_to_d_interval):
            self.max_l_to_d_interval = len

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
    def set_rrn(self, cd):
        if self.is_same_direction(cd):
            current_rrn = Logic.max_amplitude_length(cd)
        else:
            current_rrn = Logic.amplitude_length_for_long(cd, self.breakthrough_direction)
        if (self.rrn is None) or current_rrn > self.rrn:
            self.rrn = current_rrn

    """
    设置情况二开仓需要的ln_price
    """

    def set_ln_price(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
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
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            if (self.extremum_d_price is None) or dn.high > self.extremum_d_price:
                self.extremum_d_price = dn.high
        else:
            if (self.extremum_d_price is None) or dn.low < self.extremum_d_price:
                self.extremum_d_price = dn.low

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

    def histoty_status_none(self, cd, line):
        self.set_break_through_direction()
        # 设置最大的上涨幅度
        self.max_l_to_d_interval = None
        self.set_max_l_to_d_interval_data(Logic.max_amplitude_length(cd))
        # 初始化最大的下降幅度
        self.init_max_r(cd)

        # 设置参考点d
        self.reference_point_d = cd
        # 设置极限d_price
        self.extremum_d_price = None
        self.set_extremum_d(cd)
        # 设置rrn
        self.rrn = None

        self.history_status = Constants.HISTORY_STATUS_OF_TREND

    """
    初始化设置max_r
    """
    def init_max_r(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            self.max_r = max(abs(cd.start - cd.low), abs(cd.high - cd.close))     
        else:
            self.max_r = max(abs(cd.high - cd.start), abs(cd.close - cd.low))

    
    """
    趋势分析
    """
    def history_statistic_max_l_to_d(self, cd, line):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            # 方向相同统计R
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd): 
                    if cd.open == cd.low and self.last_cd.high == self.last_cd.close and cd.open >= self.last_cd.close:
                        max_l_to_d = abs(cd.high - self.last_cd.low)
                    else:  
                        max_l_to_d = Logic.max_amplitude_length(cd)   
                else:
                    if self.last_cd.close > self.last_cd.low and cd.open == cd.low and cd.open >= self.last_cd.close:
                        max_l_to_d = abs(cd.high - self.last_cd.low)
                    else:
                        max_l_to_d = Logic.max_amplitude_length(cd)
            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close > self.last_cd.low and cd.high > cd.open and cd.open >= self.last_cd.close:
                        len = abs(cd.high - self.last_cd.low)
                        max_l_to_d = max(len, abs(cd.close - cd.low))
                    else:
                        max_l_to_d = max(abs(cd.high - cd.open), abs(cd.close - cd.low))
                else:
                    if self.last_cd.high == self.last_cd.close and cd.high > cd.open and cd.open >= self.last_cd.close:
                        max_l_to_d = abs(cd.high - self.last_cd.low)
                    else:
                        max_l_to_d = max(abs(cd.high - cd.open), abs(cd.close - cd.low))
        else:
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close == self.last_cd.low and cd.open == cd.high and cd.open <= self.last_cd.close:
                        max_l_to_d = abs(self.last_cd.high - cd.low)
                    else:
                        max_l_to_d = Logic.max_amplitude_length(cd)
                else:
                    if self.last_cd.close < self.last_cd.high and cd.open == cd.high and cd.open <= self.last_cd.close:
                        max_l_to_d = abs(self.last_cd.high - cd.low)
                    else:
                        max_l_to_d = Logic.max_amplitude_length(cd)
            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close < self.last_cd.high and cd.open > cd.low and cd.open <= self.last_cd.close:
                        max_l_to_d = max(abs(self.last_cd.high - cd.low), abs(cd.high - cd.close))
                    else:
                        max_l_to_d = max(abs(cd.open - cd.low), abs(cd.high - cd.close)) 
                else:
                    if self.last_cd.close == self.last_cd.low and cd.open > cd.low and self.last_cd.close >= cd.open:
                        max_l_to_d = max(abs(self.last_cd.high - cd.low), abs(cd.high - cd.close))
                    else:
                        max_l_to_d = max(abs(cd.open - cd.low), abs(cd.high - cd.close)) 
        self.set_max_l_to_d_interval_data(max_l_to_d)

    """
    分析统计最大的max_r
    """
    def history_statistic_max_r(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if  self.last_cd.close < self.last_cd.high and cd.open > cd.low and self.last_cd.close >= cd.open:
                        max_len = max(abs(self.last_cd.high - cd.low), abs(cd.high - cd.close))
                    else:
                        max_len = max(abs(cd.open - cd.low), abs(cd.high - cd.close))
                else:
                    if self.last_cd.close == self.last_cd.low and cd.open > cd.low and self.last_cd.close >= cd.open:
                        max_len = max(abs(self.last_cd.high - cd.low), abs(cd.high - cd.close))
                        self.set_max_r(max_len)
                    else:
                        max_len = max(abs(cd.open - cd.low), abs(cd.high - cd.close))
            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close == self.last_cd.low and cd.open == cd.high and self.last_cd.close >= cd.open:
                        max_len = abs(self.last_cd.high - cd.low)
                    else:
                        max_len = Logic.max_amplitude_length(cd)
                else:
                    if self.last_cd.high > self.last_cd.close and cd.open == cd.high and self.last_cd.close >= cd.open:
                        max_len = abs(self.last_cd.high - cd.low)
                    else:
                        max_len = Logic.max_amplitude_length(cd)
        else:
            if self.is_same_direction(cd):
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close > self.last_cd.low and cd.open < cd.high and cd.open >= self.last_cd.close:
                        max_len = abs(cd.high - self.last_cd.low)
                    else:
                        max_len = max(abs(cd.high - cd.open), abs(cd.close - cd.low))
                else:
                    if self.last_cd.close == self.last_cd.high and cd.open < cd.high and cd.open >= self.last_cd.close:
                        max_len = max(abs(cd.high - self.last_cd.low), abs(cd.close - cd.low))  
                    else:
                        max_len = max(abs(cd.high - cd.open), abs(cd.close - cd.low))
            else:
                if Logic.is_same_direction_by_two_point(self.last_cd, cd):
                    if self.last_cd.close == self.last_cd.high and cd.open == cd.high and cd.open >= self.last_cd.close:
                        max_len = abs(cd.high - self.last_cd.low)
                    else:
                        max_len = Logic.max_amplitude_length(cd)
                else:
                    if self.last_cd.close > self.last_cd.low and cd.open == cd.high and cd.open >= self.last_cd.close:
                        max_len = abs(cd.high - self.last_cd.low)
                    else:
                        max_len = Logic.max_amplitude_length(cd)
        self.set_max_r(max_len)    

        # else:
        #     print('稍后进行')

        # 统计小r，判断有没有出现逆趋势
    

    """
    振荡区间处理
    参考点A不存在就设置当前点为参考点A,A.open为振荡区间的参考价格
    存在参考点A就判断当前点cd是否超出了振荡区间范围，超出就检测是否满足：出现次数最多的最高点B1和最低点B2形成振荡区间，至少3次以上（通过画直线辅佐）
    满足振荡条件时就判断是否满足突破条件【cd.high - cd.low > 5 * b1_to_b2_interval】
    一旦突破就设置突破方向、参考点D、b1_price、最大下降幅度、最大上涨幅度、情况一止损点
    设置状态为非加速振荡状态，非加速振荡子状态为寻找D2
    """

    def oscillation(self, cd, temp_file, line):
        # 检查是否存在振荡区间、存在继续判断、不存在就重置
        is_oscillating_interval, b1_to_b2_interval, b_list, current_oscillation_number = \
            Logic.check_oscillating_interval(self.oscillating_interval_list)
        if is_oscillating_interval and self.last_oscillation_number < current_oscillation_number:
            self.close_a_position_by_oscillation_number(cd, temp_file, line)
            # 设置上次振荡次数为
            #  完成突破
            self.b1_to_b2_interval = b1_to_b2_interval
            self.b_list = b_list
            if Logic.has_break_through(cd, self.b1_to_b2_interval):
                self.last_oscillation_number = current_oscillation_number
                # 设置突破方向
                self.set_b1_price(cd)
                # 先判断是否存在逆趋势要平仓，然后再重置方向
                self.set_break_through_direction_and_b1_price(cd)
                # 设置逆趋势状态
                self.counter_trend_status = Constants.STATUS_COUNTER_TREND_NO
                # 设置是否需要检测振荡状态
                self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_NO
                # 设置参考点d
                self.reference_point_d = cd
                # 设置极限d_price
                self.extremum_d_price = None
                self.set_extremum_d(cd)
                # 设置最大的下降幅度
                self.max_r = None
                self.set_max_r(cd, self.is_same_direction(cd))
                # # 设置最低点为None
                self.lowest_point_l = None
                #  设置ln_price = None
                self.ln_price = None
                # 设置最大的上涨幅度
                self.max_l_to_d_interval = None
                self.set_max_l_to_d_interval_data(cd)
                # 设置ln_price
                self.stop_loss_ln_price = cd.close
                # 设置非加速振荡寻找d2的情况
                self.set_status(Constants.NON_ACCELERATING_OSCILLATION)
                self.set_non_accelerating_oscillation_sub_status(Constants.SUB_STATUS_OF_D2)
                self.write_to_temp(temp_file, line, Constants.INDEX_B1_LINE, 0, 0, self.b1_price,
                                   len(self.oscillating_interval_list))
                # 设置情况1的状态为寻找D2
                self.set_s1_status(Constants.SITUATION_ONE_STATUS_OF_D2)
            else:
                self.oscillating_interval_list.append(cd)
        else:
            self.oscillating_interval_list.append(cd)

    """
    当振荡次数超过前面的振荡次数时，如果存在逆趋势、情况一、二没有平仓的，就进行平仓
    如果情况一跟情况二出现了平仓，将状态设置为平仓关闭状态
    """
    def close_a_position_by_oscillation_number(self, cd, temp_file, line):
        if self.need_check_oscillation_status == Constants.NEED_CHECK_OSCILLATION_STATUS_YES:
            if self.need_day_close:
                self.action_close_long_or_short(cd, cd.close, Constants.ACTIONS_INDEX_DEFAULT)
                self.write_to_temp(temp_file, line, Constants.INDEX_COUNTER_TREND_CLOSE_A_POSITION, 0,
                                   cd.close, Logic.diff_minutes(cd.datetime, cd.datetime)
                                   )
                self.need_day_close = False
            last_oscillation_cd = cd
            if self.s1_need_day_close:
                self.action_close_long_or_short(last_oscillation_cd, last_oscillation_cd.close,
                                                Constants.ACTIONS_INDEX_ONE)
                if self.in_a_counter_trend():
                    self.write_to_temp(
                        temp_file, line, Constants.REVERSE_STOP_SURPLUS_ONE, 0, last_oscillation_cd.close)
                else:
                    self.write_to_temp(temp_file, line, Constants.STOP_SURPLUS_ONE, 0, last_oscillation_cd.close)
                self.s1_need_day_close = False
                self.set_s1_status(Constants.SITUATION_ONE_STATUS_OF_CLOSE)
            if self.s2_need_day_close:
                self.action_close_long_or_short(last_oscillation_cd, last_oscillation_cd.close,
                                                Constants.ACTIONS_INDEX_TWO)
                if self.in_a_counter_trend():
                    self.write_to_temp(
                        temp_file, line, Constants.REVERSE_STOP_SURPLUS_TWO, 0, last_oscillation_cd.close)
                else:
                    self.write_to_temp(temp_file, line, Constants.STOP_SURPLUS_TWO, 0, last_oscillation_cd.close)
                self.s2_need_day_close = False
                self.set_s2_status(Constants.SITUATION_TWO_STATUS_OF_CLOSE)

    """
    无状态时候，直接为真
    需要检测逆趋势状态时，当前振荡出现的次数最大值大于上次振荡出现的最大值就为真，否则为假
    """

    def check_last_last_oscillation_number(self, last_oscillation_number):
        if self.current_status == Constants.STATUS_NONE:
            return True
        if self.counter_trend_status == Constants.STATUS_COUNTER_TREND_YES:
            if last_oscillation_number > self.last_oscillation_number:
                return True
            else:
                return False

        return False

    """
    根据b1_price获取偏移量
    """

    def get_close_a_position_offset_by_b1_price(self):
        for i in self.oscillating_interval_list:
            if i.high >= self.b1_price >= i.low:
                return i
        return None

    """
    设置突破方向
    向上就是开多的过程
    向下就是开空的过程
    """

    def set_b1_price(self, cd):
        if cd.close > cd.open:
            self.b1_price = max(self.b_list)
        else:
            self.b1_price = min(self.b_list)

    """
    设置突破方向
    向上就是开多的过程
    向下就是开空的过程
    """

    def set_break_through_direction(self, cd):
        if cd.close > cd.open:
            self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
        else:
            self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN

    """
    设置最小的ln
    """

    def set_lowest_point_l(self, cd):
        if self.lowest_point_l is None:
            self.lowest_point_l = cd
        else:
            if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
                if cd.low < self.lowest_point_l.low:
                    self.lowest_point_l = cd
            else:
                if cd.high > self.lowest_point_l.high:
                    self.lowest_point_l = cd

    """
    设置最大的dn_to_ln
    当dn_to_ln_max的值为None的时候，设置为极致点D对应数值
    """
    def set_max_r(self, len):
        if self.max_r == None or self.max_r < len:
            self.max_r = len

    """\
    非振荡加速
    """

    def non_accelerating_oscillation(self, cd, temp_file, line):
        # 判断是否为非加速振荡的逆趋势阶段
        if self.need_check_oscillation_status == Constants.NEED_CHECK_OSCILLATION_STATUS_YES:
            self.oscillation(cd, temp_file, line)
        self.new_work_non_accelerating_oscillation(cd, temp_file, line)


    """
    新版本非加速振荡
    """

    def new_work_non_accelerating_oscillation(self, cd, temp_file, line):
        # 刷新最低的低点
        self.set_lowest_point_l(cd)
        # 执行情况一的逻辑
        self.situation1(cd, temp_file, line)
        # 逆趋势逻辑x
        self.counter_trend(cd, temp_file, line)

        # 止盈或者止损完成后的重置
        self.init_after_stop_loss_or_surplus_or_reverse(cd, temp_file, line)

        # 非加速振荡状态，检查是否进入振荡b1范围内，如果没有就进行周期循环
        if self.current_status == Constants.NON_ACCELERATING_OSCILLATION:
            if Logic.need_restart(cd, self.breakthrough_direction,
                                  self.b1_price) and self.non_accelerating_oscillation_sub_status == Constants.SUB_STATUS_OF_D2:
                self.restart()
            else:
                self.refresh_cycle_parameters(cd)

    """
    情况一的逻辑
    """

    def situation1(self, cd, temp_file, line):
        if self.s1_status == Constants.SITUATION_ONE_STATUS_OF_D2:
            if self.can_run_situation_1_or_2(cd):
                if Logic.situation1(cd, self.breakthrough_direction, self.reference_point_d):
                    self.situation1_operation(cd, temp_file, line)
                    # 需要判断是否止盈或止损
                    # self.stop_surplus_or_loss_situation1(cd, temp_file, line)
        elif self.s1_status == Constants.SITUATION_ONE_STATUS_OF_STOP_SURPLUS_OR_LOSS:
            # 情况一止盈或者止损
            self.stop_surplus_or_loss_situation1(cd, temp_file, line)

    """
    情况二的逻辑
    """

    def situation2(self, cd, temp_file, line):
        if self.s2_status == Constants.SITUATION_TWO_STATUS_OF_D2:
            if self.can_run_situation_1_or_2(cd):
                if not self.is_same_direction(cd):
                    self.situation2_init(cd)
        elif self.s2_status == Constants.SITUATION_TWO_STATUS_OF_WAIT_OPEN_A_POSITION:
            if not Logic.is_counter_trend(cd, self.max_l_to_d_interval,
                                      self.breakthrough_direction) and Logic.situation2_open_a_position(
                    cd,
                    self.breakthrough_direction,
                    self.stop_loss_ln_price,
                    self.situation2_max_l_to_h):
                # 情况二开仓
                self.situation2_operation(cd, temp_file, line)
                # 情况二止盈或止损
                # self.stop_surplus_or_loss_situation2(cd, temp_file, line)
        elif self.s2_status == Constants.SITUATION_TWO_STATUS_OF_STOP_SURPLUS_OR_LOSS:  # 情况二止盈或止损
            # 先处理止盈
            self.stop_surplus_or_loss_situation2(cd, temp_file, line)

    """
    判断是否要进入情况一跟情况二的逻辑
    """

    def can_run_situation_1_or_2(self, cd):
        if not Logic.is_counter_trend(cd, self.max_l_to_d_interval,
                                      self.breakthrough_direction) and not Logic.need_restart(cd,
                                                                                              self.breakthrough_direction,
                                                                                              self.b1_price):
            return True
        else:
            return False

    """
    逆趋势的逻辑
    无论是情况一还是情况二，逆趋势同时出现，因为R是从突破后不会刷新
    """

    def counter_trend(self, cd, temp_file, line):
        if Logic.is_counter_trend(cd, self.max_l_to_d_interval, self.breakthrough_direction):
            self.set_non_accelerating_oscillation_sub_status(
                Constants.COUNTER_TREND)
            self.set_s1_status(Constants.SITUATION_ONE_REVERSE_OPEN_A_POSITION)
        if self.non_accelerating_oscillation_sub_status == Constants.COUNTER_TREND:
            self.init_counter_trend(cd)
            self.counter_trend_open_a_position(cd, temp_file, line)
        elif self.non_accelerating_oscillation_sub_status == Constants.COUNTER_TREND_CLOSE_A_POSITION:
            self.counter_trend_close_a_position(cd, temp_file, line)

    """
    重新设置循环参数
    设置最大的上涨区间
    刷新最大的下降幅度
    设置止损点
    """

    def refresh_cycle_parameters(self, cd):
        # 设置最大的上涨空间
        if self.is_same_direction(cd):
            self.set_max_l_to_d_interval_data(cd)

        # 设置最大的r_max
        self.set_max_r(cd, self.is_same_direction(cd))

        # 刷新最大的上涨幅度，跟ln
        self.set_situation2_max_l_to_h(cd)
        self.set_ln_price(cd)

        # 设置止损点
        if self.exceed_extremum_d(cd):
            self.set_stop_loss_ln(cd)
            # 重置极限值d
            self.set_extremum_d(cd)
        else:
            self.set_rrn(cd)

    """
    设置逆趋势需要的max_r
    当回调大于max_r或者回调大于rrn的时候就平仓
    """

    def old_set_max_r(self, cd):
        current_r = abs(cd.high - cd.low)
        if (self.max_r is None) or current_r > self.max_r:
            self.max_r = current_r

    """
    止盈或者止损后逻辑判断
    如果是止盈结束状态，判断是否还有试错机会，有机会之后判断，当前点是否在b1_price之上（以顺趋势为例）就重置数据,设置为寻找D2状态，进入新周期
    如果低于b1_price就检查后后面的点是否进入逆趋势，同时开启振荡检测，如果新出现振荡就进入新的振荡周期，如果出现逆趋势，就进入逆趋势逻辑
    没有试错机会就重新开始振荡检测
    """

    def init_after_stop_loss_or_surplus_or_reverse(self, cd, temp_file, line):
        if self.non_accelerating_oscillation_sub_status == Constants.STOP_SURPLUS_FINISH:
            if self.has_opportunity(cd):
                if self.exceed_extremum_d(cd):
                    self.extremum_d = cd
                self.refresh_start_data(self.extremum_d)
            else:
                # 当前l点低于b1点的时候,重新从0开始进入振荡
                self.restart()

    """
    逆趋势开仓
    """

    def counter_trend_open_a_position(self, cd, temp_file, line):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_DOWN:
            open_a_position_price = cd.high - self.max_l_to_d_interval
        else:
            open_a_position_price = cd.low + self.max_l_to_d_interval
        annotation_index = self.get_annotation_index_for_counter_trend()
        self.write_to_temp(temp_file, line, annotation_index, open_a_position_price)
        # 设置为寻找止盈状态
        self.set_non_accelerating_oscillation_sub_status(
            Constants.COUNTER_TREND_CLOSE_A_POSITION)
        # 设置为开仓状态
        self.set_s1_status(Constants.SITUATION_ONE_REVERSE_OPEN_A_POSITION)
        # 写入动作
        self.action_open_long_or_short(cd, open_a_position_price, Constants.ACTIONS_INDEX_DEFAULT)
        # 设置日结束平仓
        self.need_day_close = True

        # 设置最大的上涨幅度
        self.max_l_to_d_interval = None
        self.set_max_l_to_d_interval_data(cd)

    """
    在有试错机会的前提下判断是否满足情况一跟情况二条件
    """

    def has_opportunity(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            if cd.low > self.b1_price:
                return True
            else:
                return False
        else:
            if cd.high < self.b1_price:
                return True
            else:
                return False

    """
    止盈或者止损后，当前的l点的位置低于b1时就开启
    """

    def no_opportunity_init(self):
        if self.need_check_oscillation_status == Constants.NEED_CHECK_OSCILLATION_STATUS_NO:
            # 开启振荡检测，如果先进入振荡，就结束了
            self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_YES
            self.reset_reference_point_a()

    """
    情况一止盈或止损逻辑
    如果满足止盈条件，就写入止盈注释到文件，重置最大的下降幅度、设置为不需要检测日结束平仓
    如果满足止损状态，进写入止损注释到文件。同样初始化部分数据，
    止盈止损后都要进行逆趋势判读，满足逆趋势就进入逆趋势逻辑
    """

    def stop_surplus_or_loss_situation1(self, cd, temp_file, line):
        if Logic.stop_surplus(cd, self.breakthrough_direction, self.max_r):
            stop_surplus_price = self.get_stop_surplus_price(cd)
            if self.in_a_counter_trend():
                self.write_to_temp(
                    temp_file, line, Constants.REVERSE_STOP_SURPLUS_ONE, 0, stop_surplus_price)
            else:
                self.write_to_temp(temp_file, line, Constants.STOP_SURPLUS_ONE, 0, stop_surplus_price)
            self.set_non_accelerating_oscillation_sub_status(
                Constants.STOP_SURPLUS_FINISH)
            self.after_stop_surplus_or_stop(Constants.ACTIONS_INDEX_ONE)
            # 判断是否进入逆趋势
            self.set_s1_status(Constants.SITUATION_ONE_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH)
            if Logic.is_counter_trend(cd, self.max_l_to_d_interval, self.breakthrough_direction):
                # 设置为逆趋势状态
                self.set_non_accelerating_oscillation_sub_status(Constants.COUNTER_TREND)
            # 止盈或止损动作
            self.action_close_long_or_short(cd, stop_surplus_price, Constants.ACTIONS_INDEX_ONE)
        elif Logic.situation1_stop_loss(cd, self.stop_loss_ln_price, self.breakthrough_direction):
            if self.in_a_counter_trend():
                self.write_to_temp(
                    temp_file, line, Constants.REVERSE_STOP_LOSS_ONE, self.stop_loss_ln_price)
            else:
                self.write_to_temp(temp_file, line, Constants.STOP_LOSS_ONE, self.stop_loss_ln_price)

            self.set_non_accelerating_oscillation_sub_status(Constants.STOP_SURPLUS_FINISH)
            self.set_s1_status(Constants.SITUATION_ONE_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH)
            # 止损之后的逻辑
            self.after_stop_surplus_or_stop(Constants.ACTIONS_INDEX_ONE)
            if Logic.is_counter_trend(cd, self.max_l_to_d_interval, self.breakthrough_direction):
                # 设置为逆趋势状态
                self.set_non_accelerating_oscillation_sub_status(Constants.COUNTER_TREND)
            # 止盈或止损动作
            self.action_close_long_or_short(cd, self.stop_loss_ln_price, Constants.ACTIONS_INDEX_ONE)

    """
    情况二止盈或者止损
    如果满足止盈条件，就写入止盈注释到文件，重置最大的下降幅度、设置为不需要检测日结束平仓
    如果满足止损状态，进写入止损注释到文件。同样初始化部分数据，止损条件为当前点cd.close < ln -1 [以开多为例]
    止盈止损后都要进行逆趋势判读，满足逆趋势就进入逆趋势逻辑
    """

    def stop_surplus_or_loss_situation2(self, cd, temp_file, line):
        # if not self.is_same_direction(cd):
        if Logic.stop_surplus(cd, self.breakthrough_direction, self.max_r):
            stop_surplus_price = self.get_stop_surplus_price(cd)
            if self.in_a_counter_trend():
                self.write_to_temp(temp_file, line, Constants.REVERSE_STOP_SURPLUS_TWO, 0, stop_surplus_price)
            else:
                self.write_to_temp(temp_file, line, Constants.STOP_SURPLUS_TWO, 0, stop_surplus_price)
            # 止盈之后的动作
            self.set_non_accelerating_oscillation_sub_status(Constants.STOP_SURPLUS_FINISH)
            self.set_s2_status(Constants.SITUATION_TWO_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH)
            self.after_stop_surplus_or_stop(Constants.ACTIONS_INDEX_TWO)
            if Logic.is_counter_trend(cd, self.max_l_to_d_interval, self.breakthrough_direction):
                # 设置为逆趋势状态
                self.set_non_accelerating_oscillation_sub_status(
                    Constants.COUNTER_TREND)
            # 止盈或者止损动作
            self.action_close_long_or_short(cd, stop_surplus_price, Constants.ACTIONS_INDEX_TWO)
        # 情况二止损
        elif Logic.situation2_stop_loss(cd, self.breakthrough_direction, self.stop_loss_ln_price):
            stop_loss_price = self.get_situation2_stop_loss_price(cd)
            if self.in_a_counter_trend():
                self.write_to_temp(temp_file, line, Constants.REVERSE_STOP_LOSS_TWO, 0, stop_loss_price)
            else:
                self.write_to_temp(temp_file, line, Constants.STOP_LOSS_TWO, 0, stop_loss_price)
            self.set_non_accelerating_oscillation_sub_status(Constants.STOP_SURPLUS_FINISH)
            self.set_s2_status(Constants.SITUATION_TWO_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH)
            # 止损之后的逻辑
            self.after_stop_surplus_or_stop(Constants.ACTIONS_INDEX_TWO)
            if Logic.is_counter_trend(cd, self.max_l_to_d_interval, self.breakthrough_direction):
                # 设置为逆趋势状态
                self.set_non_accelerating_oscillation_sub_status(
                    Constants.COUNTER_TREND)
            # 止盈或者止损动作
            self.action_close_long_or_short(cd, stop_loss_price, Constants.ACTIONS_INDEX_TWO)

    """
    逆趋势平仓
    """

    def counter_trend_close_a_position(self, cd, temp_file, line):
        if self.can_close_a_position_for_counter_trend(cd):
            close_a_position_price = self.get_counter_trend_close_a_position_price(cd)
            self.write_to_temp(temp_file, line, Constants.INDEX_COUNTER_TREND_CLOSE_A_POSITION, 0,
                               close_a_position_price)
            # 止盈或者止损动作
            self.action_close_long_or_short(cd, close_a_position_price, Constants.ACTIONS_INDEX_DEFAULT)
            self.set_non_accelerating_oscillation_sub_status(Constants.STOP_SURPLUS_FINISH)
            # 设置为非逆趋势状态
            self.set_counter_trend_status(Constants.STATUS_COUNTER_TREND_NO)
            self.rrn = None
            self.need_day_close = False

    """
    获取逆趋势的平仓价格
    """

    def get_counter_trend_close_a_position_price(self, cd):
        d_close_price = self.reference_point_d.close
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
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
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            return max(self.reference_point_d.high, cd.low)
        else:
            return min(self.reference_point_d.low, cd.high)

    """
    情况一开仓要处理的操作
    写入开仓注释到文件中
    设置非加速振荡子状态为情况一止盈或者止损状态
    写入action到统计list
    设置需要考虑日结束平仓
    """

    def situation1_operation(self, cd, temp_file, line):
        # 情况1 开仓
        situation1_open_a_position_price = self.get_situation1_open_a_position_price(cd)
        annotation_index = self.get_annotation_index_for_situation1_open_a_position()
        self.write_to_temp(temp_file, line, annotation_index, situation1_open_a_position_price)
        # 设置为寻找止盈状态
        self.set_s1_status(Constants.SITUATION_ONE_STATUS_OF_STOP_SURPLUS_OR_LOSS)
        # 写入动作
        self.action_open_long_or_short(cd, situation1_open_a_position_price, Constants.ACTIONS_INDEX_ONE)
        # 设置日结束平仓
        self.s1_need_day_close = True

    """
    获取注释索引
    逆趋势中，如果是开多，就是逆趋势情况一开多，否则就是逆趋势情况一开空
    顺趋势中，如果开多，就是情况一开多，否则就是情况一开空
    """

    def get_annotation_index_for_situation1_open_a_position(self):
        if self.in_a_counter_trend():
            if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
                index = Constants.REVERSE_OPEN_A_POSITION_ONE_LONG
            else:
                index = Constants.REVERSE_OPEN_A_POSITION_ONE_SHORT
        else:
            if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
                index = Constants.OPEN_A_POSITION_ONE_LONG
            else:
                index = Constants.OPEN_A_POSITION_ONE_SHORT
        return index

    """
    获取逆趋势开仓的注释
    """

    def get_annotation_index_for_counter_trend(self):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            index = Constants.INDEX_COUNTER_TREND_LONG
        else:
            index = Constants.INDEX_COUNTER_TREND_SHORT
        return index

    """
    止盈或者止损之后，根据动作索引，将对应的平仓判断参数设置为False
    """

    def after_stop_surplus_or_stop(self, actions_index):
        if actions_index == Constants.ACTIONS_INDEX_DEFAULT:
            self.need_day_close = False
        elif actions_index == Constants.ACTIONS_INDEX_ONE:
            self.s1_need_day_close = False
        elif actions_index == Constants.ACTIONS_INDEX_TWO:
            self.s2_need_day_close = False

    """
    通过最低点位设置b1_price
    """

    def set_b1_price_by_lowest_point_l(self):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            self.b1_price = self.lowest_point_l.low
        else:
            self.b1_price = self.lowest_point_l.high

    """
    进入情况二初始化设置stop_loss_ln_price
    以及situation2_max_l_to_h
    """

    def situation2_init(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            self.stop_loss_ln_price = cd.low
        else:
            self.stop_loss_ln_price = cd.high
        self.situation2_max_l_to_h = abs(cd.high - cd.low)
        self.set_s2_status(Constants.SITUATION_TWO_STATUS_OF_WAIT_OPEN_A_POSITION)

    """
    情况二开仓操作
    写入注释到文件、设置非加速振荡子状态为止盈或者止损情况二状态
    写入开空或者开多动作
    设置日结束平仓为需要考虑平仓
    """

    def situation2_operation(self, cd, temp_file, line):
        open_a_position_price = self.situation2_open_a_position_price(cd)
        annotation_index = self.get_annotation_index_for_situation2_open_a_position()
        self.write_to_temp(temp_file, line, annotation_index, open_a_position_price)

        self.set_s2_status(Constants.SITUATION_TWO_STATUS_OF_STOP_SURPLUS_OR_LOSS)
        # 添加动作
        self.action_open_long_or_short(cd, open_a_position_price, Constants.ACTIONS_INDEX_TWO)
        # 设置日结束平仓为需要考虑平仓
        self.s2_need_day_close = True

    """
    获取注释索引
    逆趋势中，如果是开多，就是逆趋势情况二开多，否则就是逆趋势情况二开空
    顺趋势中，如果开多，就是情况二开多，否则就是情况二开空
    """

    def get_annotation_index_for_situation2_open_a_position(self):
        if self.in_a_counter_trend():
            if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
                index = Constants.REVERSE_OPEN_A_POSITION_TWO_LONG
            else:
                index = Constants.REVERSE_OPEN_A_POSITION_TWO_SHORT
        else:
            if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
                index = Constants.OPEN_A_POSITION_TWO_LONG
            else:
                index = Constants.OPEN_A_POSITION_TWO_SHORT
        return index

    """
    设置止盈价格
    """

    def get_stop_surplus_price(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            return cd.high - self.max_r
        else:
            return cd.low + self.max_r

    """
    获取情况二的止损价，以止损点对应价位为止损价
    """

    def get_situation2_stop_loss_price(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            return min(self.stop_loss_ln_price, cd.high)
        else:
            return max(self.stop_loss_ln_price, cd.low)

    """
    情况二开盘价
    """

    def situation2_open_a_position_price(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            return cd.low + self.situation2_max_l_to_h
        else:
            return cd.high - self.situation2_max_l_to_h

    """
    开空或者开多动作
    振荡向上时开多
    振荡向下时开空
    """

    def action_open_long_or_short(self, cd, price, actions_index):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
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
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
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
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            if cd.high > self.extremum_d_price:
                return True
            else:
                return False
        else:
            if cd.low < self.extremum_d_price:
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
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            self.max_r = abs(cd.high - cd.close)
        else:
            self.max_r = abs(cd.low - cd.close)

    """
    改变方向
    """

    def reverse_direct(self):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
        elif self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_DOWN:
            self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP

    """
    没有试错机会重新开始
    """

    def restart(self):
        self.oscillating_interval_list = []
        self.reference_point_d = None  # 振荡的参考点D
        self.extremum_d_price = None  # 设置极值d_price为None
        self.b1_to_b2_interval = None
        self.b1_price = None  # b1的close值
        self.breakthrough_direction = None  # 突破的方向 -1 向下 1 向上

        self.non_accelerating_oscillation_sub_status = None

        self.stop_loss_ln_price = None  # 情况一的止损点价位

        self.lowest_point_l = None  # l的最地点

        self.max_l_to_d_interval = None  # 最大上涨的间隔

        self.current_status = Constants.STATUS_NONE  # 当前状态

        self.counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态
        self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_NO  # 振荡检测
        self.ln_price = None  # 情况二需要的止损价格
        self.situation2_max_l_to_h = None  # 情况二需要的最大上涨幅度
        self.oscillating_interval_list = []
        self.max_r = None

        # 设置状态为None
        self.s1_status = None
        self.s2_status = None

        # 设置rrn为None
        self.rrn = None

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
        if cd.close > cd.open and self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            return True
        elif cd.close < cd.open and self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_DOWN:
            return True
        else:
            return False

    """
    一行行地读取文件数据并且分析
    """

    def analysis(self, bar, temp_file):
        line = Logic.format_bar_data_to_line(bar)
        self.has_current_line_written = False
        try:
            cd = Logic.bar_to_data_object(bar)  # 当前时间单位的相关数据
        except:
            # print("skipping line: " + line) # 略过csv的header
            print(f"读取数据出错了...")
            return
        # 判断是否为一天的起始点。实盘开盘时间为21:00:00
        if Logic.is_firm_offer_start_minute(cd.datetime):
            self.restart()
            
        # 如果是当天收盘前的最后一分钟，主动平仓
        if Logic.is_last_minute(cd.datetime):
            self.last_minute_of_the_day(cd, temp_file, line)
        elif self.current_status == Constants.STATUS_NONE:  # 寻找振荡
            self.status_none(cd, temp_file, line)
        elif self.current_status == Constants.NON_ACCELERATING_OSCILLATION:  # 非加速振荡
            self.non_accelerating_oscillation(cd, temp_file, line)
        # 将没有任何状态/动作的数据行也写入到临时文件中
        if not self.has_current_line_written:
            self.write_to_temp(temp_file, line, Constants.INDEX_OBSERVE)

        self.test_count += 1

    """
    历史行情数据分析
    """
    def history_analysis(self, vt_symbol, frequent):
        try:
           data_file = open('C:/Users/Administrator/strategies/data/' + f"{vt_symbol}_{frequent}m.csv", 'r')
        except:
            print(f"无法打开{vt_symbol}_{frequent}m.csv文件")
            os._exit(0)
        while True:
            line = data_file.readline()
            if not line:
                break

            temp_array = line.split(',')
            self.has_current_line_written = False
            if len(temp_array) > 0:
                try:
                    cd = Logic.raw_to_data_object(
                        temp_array, count, line)  # 当前时间单位的相关数据
                except:
                    continue
                
                if self.history_status == Constants.HISTORY_STATUS_OF_NONE: 
                    self.histoty_status_none(cd, line)
                elif self.history_status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
                    self.non_accelerating_oscillation(cd, temp_file, line)
            # 将没有任何状态/动作的数据行也写入到临时文件中
            if not self.has_current_line_written:
                self.write_to_temp(temp_file, line, Constants.INDEX_OBSERVE)
            count += 1

        data_file.close()
        #  情况一 + 情况二 + 逆趋势
        actions = self.s1_actions + self.s2_actions + self.actions
        # actions = self.actions
        Logic.calculate_rate(actions, os.path.basename(self.filename))
        self.actions.clear()
 
