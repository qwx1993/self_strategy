from ast import Constant
from doctest import FAIL_FAST
from types import SimpleNamespace
from datetime import datetime

from self_strategy.constants import Constants

class TickLogic:

    """
    判断是否保持方向不变
    """
    def keep_direction(cd, ls):
        first = ls[0]
        last = ls[-1]
        if first.current <= last.current <= cd.current:
            return True
        elif first.current >= last.current >= cd.current:
            return True
        else:
            return False 
    
    """
	将csv数据文件中的一行数据转变成一个时间单位的价格信息object
	order_book_id,datetime,last
	SA2301,2022-08-26 21:01:00,2420.0,2424.0,2413.0,2415.0
	"""
    def tick_price_to_data_object(temp_array, line_count, raw_string):
        current_price = float(temp_array[2])

        current = SimpleNamespace()
        current.datetime = temp_array[1]
        current.current = current_price
        current.line = line_count

        current.raw_string = raw_string

        return current

    
    """
	reference时间和target时间之间的间隔[单位秒]
	"""
    def diff_seconds(reference, target):
        decimal = 0
        decimal_str = '.500000'
        if reference.find(decimal_str) > 0:
            reference = reference.replace(decimal_str, '')
            decimal = 0.5
        if target.find(decimal_str) > 0:
            target = target.replace(decimal_str, '')
            decimal -= 0.5
        reference_obj = datetime.strptime(reference, '%Y-%m-%d %H:%M:%S')
        target_obj = datetime.strptime(target, '%Y-%m-%d %H:%M:%S')
        diff = abs(reference_obj - target_obj).total_seconds()
        return diff + decimal
    
    
    """
    是否进入逆趋势
    逆趋势判断条件，统计整个过程的最大上涨幅度max_l_to_d_interval，如果当前下降幅度 > max_l_to_d_interval
    就进入逆趋势

    """
    def is_counter_trend(ls, max_l_to_d_interval, max_l_to_d_k):
        current_length, current_k = TickLogic.amplitude_length_and_k(ls)
        if current_length >= max_l_to_d_interval and current_k >= max_l_to_d_k:
            print(f"逆趋势 => {ls} k => {current_k} | {current_length} max_l_to_d_k => {max_l_to_d_k} | {max_l_to_d_interval}")
            return True
        else:
            return False
    # def is_counter_trend(max_l_to_d_interval, max_l_to_d_k, max_r, max_r_k):
    #     if max_r >= max_l_to_d_interval and max_r_k >= max_l_to_d_k:
    #         return True
    #     else:
    #         return False


    """
    获取长度跟斜率
    """
    def amplitude_length_and_k(ls):
        first_cd = ls[0]
        last_cd = ls[-1]
        amplitude_length = abs(first_cd.current - last_cd.current)

        return amplitude_length, amplitude_length / TickLogic.diff_seconds(last_cd.datetime, first_cd.datetime)

    """
    是否可以开仓
    """
    def can_open_a_price(h_price, counter_trend_status):
        if not h_price is None and counter_trend_status == Constants.STATUS_COUNTER_TREND_YES:
            return True
        else:
            return False
    
    """
	将tick数据合成分钟数据
	"""
    def merge_ticks_to_m1(ticks):
        l = len(ticks)
        if l < 2:
            return None
        merged = SimpleNamespace()
        merged.open = ticks[0].current
        merged.close = ticks[l-1].current
        merged.high = ticks[0].current
        merged.low = ticks[0].current
        merged.flunc = abs(ticks[0].current - ticks[l-1].current)
        for i in range(len(ticks)):
            if ticks[i].current > merged.high:
                merged.high = ticks[i].current
            if ticks[i].current < merged.low:
                merged.low = ticks[i].current
        merged.direction = TickLogic.get_direction_value(merged.open, merged.close)
        merged.datetime = datetime.strptime(ticks[0].datetime, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:00")

        return merged
    
    """
    定方向
    """ 
    def get_direction_value(opening_price, closing_price):
        if closing_price > opening_price:
            return Constants.DIRECTION_UP
        elif closing_price < opening_price:
            return Constants.DIRECTION_DOWN
        else:
            return Constants.DIRECTION_NONE