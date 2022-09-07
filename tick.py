"""
"""
import os
import sys
from logic import Logic
from tick_logic import TickLogic
from constants import Constants


class Tick:
    reference_point_d = None  # 振荡的参考点D
    d_index = 1  # d标注点索引
    b1_to_b2_interval = None  # 振荡区间的最大值跟最小值的距离
    b_list = []  # b1的close值
    last_line_list = []
    breakthrough_direction = None  # 突破的方向 -1 开空 1 开多
    sub_status = None  # 非加速振荡子状态
    direction_type = None  # 走势方向，以顺趋势为参考
    d_to_l = []  # d到l元素记录
    l_to_d = [] # l到d元素记录

    # 情况一的参数
    stop_loss_ln_price = None  # 情况一的止损点价位，出现新的dn才重置
    s1_status = None  # 情况一的状态
    ln_price = None  # 用作情况二的止损价格, 止损点为ln - 1
    b1_price = None  # b1点的价位
    b2_price = None

    lowest_point_l = None  # l的最地点

    max_l_to_d_interval = None  # 最大上涨的间隔,即R
    max_l_to_d_k = None # 最大上涨的幅度的斜率
    max_r = None  # 表示从dn-ln的最大值，d1点开始
    max_r_k = None

    current_status = Constants.STATUS_NONE  # 当前状态，目前就无状态跟非加速振荡

    counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态，默认非逆趋势状态
    need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_NO  # 默认不需要检测逆趋势

    actions = []  # 记录所有的动作，包括开空，开多，逆开空，逆开多，注意：逆趋势下是两倍仓位
    s1_actions = []  # 记录所有的情况一动作
    s2_actions = []  # 记录所有的情况二动作
    lines_written_to_temp = 1  # 写入临时文件的行数
    has_current_line_written = False  # 当前分钟的数据行是否写到了供画图用的临时文件中
    last_line = None
    data_file = None  # 正在分析的数据文件
    stop_surplus_price = 0  # 设置止盈价
    need_day_close = False  # 是否需要平仓、True需要、False不需要
    s1_need_day_close = False
    s2_need_day_close = False
    extremum_d = None  # 极值点D
    situation2_max_l_to_h = None  # 用作情况二的上升幅度 [对应文档中的rrn]
    last_oscillation_number = 0  # 前面振荡的次数

    s2_status = None  # 情况二的状态

    rrn = None  # 逆趋势止盈使用的参数
    price_dict = {}  # 振荡统计价格次数

    first_line_list = []


    """
    初始化
    """

    def __init__(self, filename):
        # 所有的list数据需要初始化
        self.oscillating_interval_list = []
        self.b_list = []
        self.last_line_list = []
        self.d_to_l = []  # d到l元素记录
        self.l_to_d = []  # l到d元素记录
        self.price_dict = {}  # 此参数为了优化程序允许时间
        self.first_line_list = [] # 刚开始的位置

        self.filename = filename

    """
    添加对应的动作，目前包括开空、平空、开多、平多、逆开空、逆平空、逆开多、逆平多
    逆开空、逆平空、逆开多、逆平多 时为2倍仓位
    """

    def add_action(self, cd, action, price, actions_index=Constants.ACTIONS_INDEX_DEFAULT):
        record = {
            "price": price,
            "action": action,
            "datetime": cd.time
        }

        if actions_index == Constants.ACTIONS_INDEX_DEFAULT:
            self.actions.append(record)
        elif actions_index == Constants.ACTIONS_INDEX_ONE:
            self.s1_actions.append(record)
        elif actions_index == Constants.ACTIONS_INDEX_TWO:
            self.s2_actions.append(record)
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

    def set_sub_status(self, status):
        self.sub_status = status

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
        self.stop_loss_ln_price = cd.current

    """
    设置最大的l_to_d间隔数据，以及斜率
    """

    def set_max_l_to_d_interval_data(self, ls):
        first_cd = ls[0]
        last_cd = ls[-1]
        current_l_to_d_interval = abs(last_cd.last - first_cd.last)
        if (self.max_l_to_d_interval is None) or (current_l_to_d_interval > self.max_l_to_d_interval):
            self.max_l_to_d_interval = current_l_to_d_interval
            self.max_l_to_d_k = self.max_l_to_d_interval/Logic.diff_seconds(last_cd.time, first_cd.time)

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
    def set_rrn(self, ls):
        current_rrn = Logic.amplitude_length(ls)
        if self.rrn is None or current_rrn > self.rrn:
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
    设置极值点D
    当开多的时候，大于之前的current就更新为当前值
    当开空的时候，小于之前的current就更新为当前值
    """

    def set_extremum_d(self, dn):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            if (self.extremum_d is None) or dn.current > self.extremum_d.current:
                self.extremum_d = dn
        else:
            if (self.extremum_d is None) or dn.current < self.extremum_d.current:
                self.extremum_d = dn

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
                      b1_offset=0, b2_price = 0, note=""):
        temp_file.write(line_content.rstrip() + "," + str(annotation_index) + "," + str(self.lines_written_to_temp) +
                        "," + Constants.STR_ACTIONS_AND_STATES[annotation_index]["en"] + "," + str(open_price) + "," +
                        str(stop_price) + "," + str(b1_price) + "," +
                        str(b1_offset) + "," + str(b2_price) + "," + note + "\n")
        self.lines_written_to_temp += 1
        self.has_current_line_written = True

    """
    将需要绘点的信息写入到此文件中
    """
    def write_to_point_temp(self, point_temp_file, time, annotation_index, x_coordinate=0, y_coordinate=0):
        point_temp_file.write(
            str(time) + "," + str(annotation_index) + "," + Constants.STR_ACTIONS_AND_STATES[annotation_index]["en"] +
            "," + str(x_coordinate) + "," + str(y_coordinate) + "," + "\n")
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
        self.action_close_long_or_short(cd, cd.current, actions_index)
        self.write_to_temp(temp_file, line, annotation, 0, cd.current)

    """
    当前状态为STATUS_NONE时的逻辑
    """

    def status_none(self, cd, temp_file, line):
        self.first_line(cd, temp_file, line)

    """
    振荡区间处理
    参考点A不存在就设置当前点为参考点A,A.open为振荡区间的参考价格
    存在参考点A就判断当前点cd是否超出了振荡区间范围，超出就检测是否满足：出现次数最多的最高点B1和最低点B2形成振荡区间，至少3次以上（通过画直线辅佐）
    满足振荡条件时就判断是否满足突破条件【cd.high - cd.low > 5 * b1_to_b2_interval】
    一旦突破就设置突破方向、参考点D、b1_price、最大下降幅度、最大上涨幅度、情况一止损点
    设置状态为非加速振荡状态，非加速振荡子状态为寻找D2
    """

    def first_line(self, cd, temp_file, line):
        # 设置最后上涨或下跌趋势的list
        self.set_first_line_list(cd)
        if len(self.first_line_list) >= 2:
            first_price = self.first_line_list[0].last
            last_price = self.first_line_list[-1].last

            if first_price > last_price:
                self.breakthrough_direction == Constants.DIRECTION_DOWN
            elif first_price < last_price:
                self.breakthrough_direction == Constants.DIRECTION_UP
            else:
                self.breakthrough_direction == Constants.DIRECTION_NONE

            if not self.breakthrough_direction == Constants.DIRECTION_NONE:
                # 设置d点
                  self.set_status(Constants.STATUS_FIND_D1)   
        



        # 检查是否存在振荡区间、存在继续判断、不存在就重置
        if len(self.oscillating_interval_list) > 0:
            self.price_dict = Logic.oscillating_price_dict(self.oscillating_interval_list, self.price_dict)
        # is_oscillating_interval, b1_to_b2_interval, b_list, current_oscillation_number = \
        #     Logic.check_oscillating_interval(self.price_dict)
        is_oscillating_interval, b1_to_b2_interval, b_list, current_oscillation_number = \
            Logic.check_oscillating_interval1(self.oscillating_interval_list)

        # is_oscillating_interval_old, b1_to_b2_interval_old, b_list_old, current_oscillation_number_old = \
        #     Logic.check_oscillating_interval1(self.oscillating_interval_list)
        # if current_oscillation_number_old != current_oscillation_number:
        #     print(f"err => {self.oscillating_interval_list}")
        #     print(f"start => {self.oscillating_interval_list[0].time} end => {self.oscillating_interval_list[-1].time}")
        #     sys.exit(1)
        if is_oscillating_interval and self.last_oscillation_number < current_oscillation_number:
            # self.close_a_position_by_oscillation_number(cd, temp_file, line)
            # # 设置上次振荡次数为
            if Logic.has_break_through(self.last_line_list, b1_to_b2_interval):
                # #  完成突破
                self.b1_to_b2_interval = b1_to_b2_interval
                self.b_list = b_list
                self.last_oscillation_number = current_oscillation_number
                # 设置突破方向
                self.set_b1_and_b2_price(self.last_line_list)
                # 先判断是否存在逆趋势要平仓，然后再重置方向
                self.set_break_through_direction_and_b1_price()
                # 设置逆趋势状态
                self.counter_trend_status = Constants.STATUS_COUNTER_TREND_NO
                # 设置是否需要检测振荡状态
                self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_NO
                # # 设置最低点为None
                self.lowest_point_l = None
                #  设置ln_price = None
                self.ln_price = None
                # 设置为突破寻找D2的状态
                self.set_status(Constants.STATUS_FIND_D1)
                # todo
                Logic.truncate_last_n_lines(1, temp_file)
                self.lines_written_to_temp -= 1
                self.write_to_temp(temp_file, self.last_line, Constants.INDEX_B1_AND_B2_LINE, 0, 0, self.b1_price,
                                   len(self.oscillating_interval_list), self.b2_price)
                self.has_current_line_written = False
            else:
                self.oscillating_interval_list.append(cd)
        else:
            self.oscillating_interval_list.append(cd)

    """
    突破寻找D点
    """
    def find_d(self, cd, temp_file, line):
        # 如果改变了方向，即出现了D点
        if TickLogic.keep_direction(cd, self.last_line_list):
            self.first_line_list.append(cd)
        else:
            last_cd = self.first_line_list[-1]
            # 设置参考点d1
            self.reference_point_d = last_cd
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
            # # 直接进入非加速振荡判断
            # self.non_accelerating_oscillation_for_s1(cd, temp_file, line)

    """
    最后的直线上涨或下跌记录
    """
    def set_first_line_list(self, cd):
        if len(self.first_line_list) == 0:
            self.first_line_list.append(cd)
         

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
                # 设置情况2的状态为寻找D2
                self.set_s2_status(Constants.SITUATION_TWO_STATUS_OF_D2)

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

    def set_b1_and_b2_price(self, ls):
        last_current = ls[-1].current
        first_current = ls[0].current

        if last_current > first_current:
            self.b1_price = max(self.b_list)
            self.b2_price = min(self.b_list)
            # self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
        else:
            self.b1_price = min(self.b_list)
            self.b2_price = max(self.b_list)
            # self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
    """
    设置突破方向
    向上就是开多的过程
    向下就是开空的过程
    """

    def set_break_through_direction_and_b1_price(self):
        first_current = self.last_line_list[0].current
        last_current = self.last_line_list[-1].current
        if last_current > first_current:
            self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
            self.b1_price = max(self.b_list)
        else:
            self.breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
            self.b1_price = min(self.b_list)

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

    def set_max_r(self, ls):
        current_r = Logic.amplitude_length(ls)
        if self.max_r is None or self.max_r < current_r:
            self.max_r = current_r
            first_cd_time = ls[0].time
            last_cd_time = ls[-1].time
            self.max_r_k = current_r/Logic.diff_seconds(last_cd_time, first_cd_time)


    """\
    非振荡加速
    """

    def non_accelerating_oscillation(self, cd, temp_file, line):
        # 判断是否为非加速振荡的逆趋势阶段
        self.statistic(cd, temp_file, line)
        
        # 逆趋势逻辑判断
        
    """
    新版本非加速振荡
    """

    def new_work_non_accelerating_oscillation(self, cd, temp_file, line):
        # 刷新最低的低点
        self.set_lowest_point_l(cd)
        # 执行情况一的逻辑
        self.situation1(cd, temp_file, line)
        # 执行情况二的情况
        self.situation2(cd, temp_file, line)
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
    查找l点
    """
    def non_accelerating_oscillation_for_s1(self, cd, temp_file, line):
        if self.sub_status == Constants.SUB_STATUS_OF_L1:
            self.statistic(cd, temp_file, line)

    """
    统计d跟l
    """
    def statistic(self, cd):
        if self.direction_type == Constants.DIRECTION_TYPE_OF_D_TO_L:
            keep_direction = Logic.keep_direction(cd, self.d_to_l)
            if keep_direction:
                self.d_to_l.append(cd)
            else:
                # 刷新最大下降幅度
                self.set_max_r(self.d_to_l)
                # 重置l_tp_d
                last_d_to_l_cd = self.d_to_l[-1]
                self.l_to_d = [last_d_to_l_cd, cd]
                self.direction_type = Constants.DIRECTION_TYPE_OF_L_TO_D
        elif self.direction_type == Constants.DIRECTION_TYPE_OF_L_TO_D:
            keep_direction = Logic.keep_direction(cd, self.l_to_d)
            if keep_direction:
                self.l_to_d.append(cd)
            else:
                self.set_max_l_to_d_interval_data(self.l_to_d)
                last_l_to_d = self.l_to_d[-1]
                first_l_to_d = self.l_to_d[0]
                self.d_to_l = [last_l_to_d, cd]
                self.direction_type = Constants.DIRECTION_TYPE_OF_D_TO_L
                # 判断是否极值
                if self.exceed_extremum_d(last_l_to_d):
                    self.set_stop_loss_ln(first_l_to_d)
                    # 重置极限值d
                    self.set_extremum_d(last_l_to_d)
                else:
                    self.set_rrn(self.l_to_d)

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

    def can_run_situation_1_or_2(self, cd, ls):
        if not Logic.is_counter_trend(ls, self.max_l_to_d_interval,
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

    def counter_trend_logic(self, cd, temp_file, line):
        if self.direction_type == Constants.DIRECTION_TYPE_OF_D_TO_L:
            keep_direction = Logic.keep_direction(cd, self.d_to_l)
            if keep_direction:
                self.d_to_l.append(cd)
                # 只有突破寻找L1 跟 情况一、二完成止盈或者止损后才进入逆趋势
                if self.sub_status in [Constants.SUB_STATUS_OF_L1, Constants.SUB_STATUS_OF_STOP_OR_SURPLUS_FINISH]:
                    if Logic.is_counter_trend(self.d_to_l, self.max_l_to_d_interval, self.max_l_to_d_k):
                        self.set_sub_status(Constants.SUB_STATUS_OF_COUNTER_TREND)  # 设置为逆趋势
                        self.init_counter_trend(cd)
                        self.counter_trend_open_a_position(cd, temp_file, line)
                elif self.sub_status == Constants.COUNTER_TREND_CLOSE_A_POSITION:
                    self.counter_trend_close_a_position(cd, temp_file, line)
            else:
                # 刷新最大下降幅度
                last_d_to_l = self.d_to_l[-1]
                self.l_to_d = [last_d_to_l, cd]
                self.direction_type = Constants.DIRECTION_TYPE_OF_L_TO_D
                self.set_max_r(self.d_to_l)
        elif self.direction_type == Constants.DIRECTION_TYPE_OF_L_TO_D:
            keep_direction = Logic.keep_direction(cd, self.l_to_d)
            if keep_direction:
                self.l_to_d.append(cd)
            else:
                # 重置l_tp_d
                last_l_to_d_cd = self.l_to_d[-1]
                self.d_to_l = [last_l_to_d_cd, cd]
                self.direction_type = Constants.DIRECTION_TYPE_OF_D_TO_L
                # 必须先进行D点设置
                if self.reference_point_d is None:
                    self.counter_intend_set_d()
                else:
                    if self.exceed_extremum_d(last_l_to_d_cd):
                        self.set_stop_loss_ln(last_l_to_d_cd)
                        # 重置极限值d
                        self.set_extremum_d(last_l_to_d_cd)
                    else:
                        self.set_rrn(self.l_to_d)

                if self.sub_status == Constants.COUNTER_TREND_CLOSE_A_POSITION:
                    # 判断是否平仓
                    self.counter_trend_close_a_position(cd, temp_file, line)
                # todo 判断是否极值
    """
    当逆趋势出现了，并且改变方向时，设置新的D点
    """
    def counter_intend_set_d(self):
        # 设置最大的上涨幅度
        last_cd = self.l_to_d[-1]
        self.max_l_to_d_interval = None
        self.max_l_to_d_k = None
        self.set_max_l_to_d_interval_data(self.l_to_d)
        # 设置参考点D
        self.reference_point_d = last_cd
        self.extremum_d = last_cd

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
        if self.sub_status == Constants.SUB_STATUS_OF_STOP_OR_SURPLUS_FINISH:
            if self.has_opportunity(cd):
                if self.exceed_extremum_d(cd):
                    self.extremum_d = cd
                self.refresh_start_data(self.extremum_d)
            else:
                # 当前l点低于b1点的时候,重新从0开始进入振荡
                self.restart()

    """
    止盈或者止损后逻辑判断
    如果是止盈结束状态，判断是否还有试错机会，有机会之后判断，当前点是否在b1_price之上（以顺趋势为例）就重置数据,设置为寻找D2状态，进入新周期
    如果低于b1_price就检查后后面的点是否进入逆趋势，同时开启振荡检测，如果新出现振荡就进入新的振荡周期，如果出现逆趋势，就进入逆趋势逻辑
    没有试错机会就重新开始振荡检测
    """

    def init_after_stop_loss_or_surplus_or_reverse_logic(self, cd, temp_file, line):
        if self.sub_status == Constants.SUB_STATUS_OF_STOP_OR_SURPLUS_FINISH:
            if self.has_opportunity(cd):
                self.refresh_start_data(self.extremum_d)
            else:
                # 当前l点低于b1点的时候,重新从0开始进入振荡
                self.restart()

    """
    逆趋势开仓
    """

    def counter_trend_open_a_position(self, cd, temp_file, line):
        open_a_position_price = cd.current
        annotation_index = self.get_annotation_index_for_counter_trend()
        self.write_to_temp(temp_file, line, annotation_index, open_a_position_price)
        # 设置为寻找止盈状态
        self.set_sub_status(Constants.COUNTER_TREND_CLOSE_A_POSITION)
        # 写入动作
        self.action_open_long_or_short(cd, open_a_position_price, Constants.ACTIONS_INDEX_DEFAULT)
        # 设置日结束平仓
        self.need_day_close = True

    """
    在有试错机会的前提下判断是否满足情况一跟情况二条件
    """

    def has_opportunity(self, cd):
        if self.breakthrough_direction == Constants.BREAKTHROUGH_DIRECTION_UP:
            if cd.current > self.b1_price:
                return True
            else:
                return False
        else:
            if cd.current < self.b1_price:
                return True
            else:
                return False

    """
    情况一止盈或止损逻辑
    如果满足止盈条件，就写入止盈注释到文件，重置最大的下降幅度、设置为不需要检测日结束平仓
    如果满足止损状态，进写入止损注释到文件。同样初始化部分数据，
    止盈止损后都要进行逆趋势判读，满足逆趋势就进入逆趋势逻辑
    """

    def stop_surplus_or_loss_situation1(self, cd, temp_file, line):
        if Logic.stop_surplus(self.d_to_l, self.max_r, self.max_r_k):
            stop_surplus_price = cd.current
            if self.in_a_counter_trend():
                self.write_to_temp(
                    temp_file, line, Constants.REVERSE_STOP_SURPLUS_ONE, 0, stop_surplus_price)
            else:
                self.write_to_temp(temp_file, line, Constants.STOP_SURPLUS_ONE, 0, stop_surplus_price)
            self.set_sub_status(Constants.SUB_STATUS_OF_STOP_OR_SURPLUS_FINISH)
            self.after_stop_surplus_or_stop(Constants.ACTIONS_INDEX_ONE)
            # 判断是否进入逆趋势
            # if Logic.is_counter_trend(self.d_to_l, self.max_l_to_d_interval, self.max_l_to_d_k):
            #     # 设置为逆趋势状态
            #     self.set_sub_status(Constants.SUB_STATUS_OF_COUNTER_TREND)
            # 止盈或止损动作
            self.action_close_long_or_short(cd, stop_surplus_price, Constants.ACTIONS_INDEX_ONE)
        elif Logic.situation1_stop_loss(cd, self.stop_loss_ln_price, self.breakthrough_direction):
            if self.in_a_counter_trend():
                self.write_to_temp(
                    temp_file, line, Constants.REVERSE_STOP_LOSS_ONE, cd.current)
            else:
                self.write_to_temp(temp_file, line, Constants.STOP_LOSS_ONE, cd.current)

            self.set_sub_status(Constants.SUB_STATUS_OF_STOP_OR_SURPLUS_FINISH)
            # print(f"情况一止损 {cd.time} stop_loss_ln_price {cd.current} => {self.direction_type}")
            # 止损之后的逻辑
            self.after_stop_surplus_or_stop(Constants.ACTIONS_INDEX_ONE)
            # if Logic.is_counter_trend(self.d_to_l, self.max_l_to_d_interval, self.max_l_to_d_k):
            #     # 设置为逆趋势状态
            #     self.set_sub_status(Constants.SUB_STATUS_OF_COUNTER_TREND)
            # 止盈或止损动作
            self.action_close_long_or_short(cd, cd.current, Constants.ACTIONS_INDEX_ONE)

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
        if self.rrn is None:
            self.rrn = self.b1_to_b2_interval
        if Logic.can_close_a_position_for_counter_trend(self.l_to_d, self.rrn):
            close_a_position_price = cd.current
            self.write_to_temp(temp_file, line, Constants.INDEX_COUNTER_TREND_CLOSE_A_POSITION, 0,
                               close_a_position_price)
            # 止盈或者止损动作
            self.action_close_long_or_short(cd, close_a_position_price, Constants.ACTIONS_INDEX_DEFAULT)
            self.set_sub_status(Constants.SUB_STATUS_OF_STOP_OR_SURPLUS_FINISH)
            # 设置为非逆趋势状态
            self.set_counter_trend_status(Constants.STATUS_COUNTER_TREND_NO)
            self.rrn = None
            self.need_day_close = False

    """
    情况一开仓要处理的操作
    写入开仓注释到文件中
    设置非加速振荡子状态为情况一止盈或者止损状态
    写入action到统计list
    设置需要考虑日结束平仓
    """

    def situation1_operation(self, cd, temp_file, line):
        # 情况1 开仓
        situation1_open_a_position_price = cd.current
        annotation_index = self.get_annotation_index_for_situation1_open_a_position()
        self.write_to_temp(temp_file, line, annotation_index, situation1_open_a_position_price)
        # 设置为寻找止盈状态
        self.set_sub_status(Constants.SUB_STATUS_OF_STOP_LOSS_OR_SURPLUS)
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
            return cd.current - self.max_r
        else:
            return cd.current + self.max_r

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
        # 改变方向类型
        self.reverse_direction_type()
        # 设置参考点d
        self.set_counter_trend_status(Constants.STATUS_COUNTER_TREND_YES)
        self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_YES
        # 重置振荡的参数
        self.oscillating_interval_list = []
        self.price_dict = {}
        self.max_r = None
        self.max_r_k = None
        self.reference_point_d = None

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
        self.reference_point_d = None  # 振荡的参考点D
        self.d_index = 1  # d标注点索引
        self.b1_to_b2_interval = None  # 振荡区间的最大值跟最小值的距离
        self.b_list = []  # b1的close值
        self.last_line_list = []
        self.breakthrough_direction = None  # 突破的方向 -1 开空 1 开多
        self.sub_status = None  # 非加速振荡子状态
        self.direction_type = None  # 走势方向，以顺趋势为参考
        self.d_to_l = []  # d到l元素记录
        self.l_to_d = []  # l到d元素记录

        # 情况一的参数
        self.stop_loss_ln_price = None  # 情况一的止损点价位，出现新的dn才重置
        self.ln_price = None  # 用作情况二的止损价格, 止损点为ln - 1
        self.b1_price = None  # b1点的价位
        self.b2_price = None

        self.lowest_point_l = None  # l的最地点

        self.max_l_to_d_interval = None  # 最大上涨的间隔,即R
        self.max_l_to_d_k = None  # 最大上涨的幅度的斜率
        self.max_r = None  # 表示从dn-ln的最大值，d1点开始
        self.max_r_k = None

        self.current_status = Constants.STATUS_NONE  # 当前状态，目前就无状态跟非加速振荡

        self.counter_trend_status = Constants.STATUS_COUNTER_TREND_NO  # 逆趋势状态，默认非逆趋势状态
        self.need_check_oscillation_status = Constants.NEED_CHECK_OSCILLATION_STATUS_NO  # 默认不需要检测逆趋势
        self.stop_surplus_price = 0  # 设置止盈价
        self.need_day_close = False  # 是否需要平仓、True需要、False不需要
        self.s1_need_day_close = False
        self.s2_need_day_close = False
        self.extremum_d = None  # 极值点D
        self.situation2_max_l_to_h = None  # 用作情况二的上升幅度 [对应文档中的rrn]

        self.s2_status = None  # 情况二的状态

        self.rrn = None  # 逆趋势止盈使用的参数
        self.oscillating_interval_list = []
        self.price_dict = {}

    """
    试错重新设置值
    """

    def refresh_start_data(self, cd):
        # 设置最大的下降幅度
        self.lowest_point_l = None
        # 设置最低点
        # 设置ln_price
        self.stop_loss_ln_price = None
        self.reference_point_d = cd
        # 设置极值d的价格
        self.set_extremum_d(cd)
        # 设置为寻找D2状态
        self.set_sub_status(Constants.SUB_STATUS_OF_L1)

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
        # self.actions = self.actions + self.s1_actions + self.s2_actions
        # self.s1_actions = []
        # self.s2_actions = []

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

    def analysis(self):
        try:
            self.data_file = open(self.filename, 'r')
        except:
            print("无法打开" + self.filename)
            os._exit(0)

        temp_file = open("temp/temp-" + os.path.basename(self.filename), "w+")
        count = 0

        # 从当前时间往回走Constants.REFERENCE_AND_SPEEDING_LENGTH个时间单位的价格相关的记录，包括开始值、结束值、波动 等

        while True:
            line = self.data_file.readline()
            if not line:
                break

            temp_array = line.split(',')
            self.has_current_line_written = False
            if len(temp_array) > 0:
                try:
                    cd = Logic.raw_to_data_object_for_tick(
                        temp_array, count, line)  # 当前时间单位的相关数据
                except:
                    # print("skipping line: " + line) # 略过csv的header
                    continue
                print(f"time => {cd.time}")
                # 如果是当天收盘前的最后一分钟，主动平仓
                if Logic.is_last_minute(cd.time):

                    self.last_minute_of_the_day(cd, temp_file, line)
                    continue

                if self.current_status == Constants.STATUS_NONE:  # 寻找振荡
                    self.status_none(cd, temp_file, line)
                elif self.current_status == Constants.STATUS_FIND_D1:  # 寻找D1
                    self.find_d(cd, temp_file, line)
                elif self.current_status == Constants.NON_ACCELERATING_OSCILLATION:  # 非加速振荡
                    self.non_accelerating_oscillation(cd, temp_file, line)
            # 将没有任何状态/动作的数据行也写入到临时文件中
            count += 1
            self.last_line = line

        self.data_file.close()
        temp_file.close()
