from types import SimpleNamespace
import os
import copy
from datetime import datetime
from datetime import timedelta
from self_strategy.constants import Constants
from self_strategy.logic import Logic
from copy import deepcopy

class QuotationLogic:

    """
    趋势分析
    """
    def get_max_l_to_d(direction, last_cd, cd):
        if direction == Constants.DIRECTION_UP:
            # 方向相同统计R
            if QuotationLogic.is_same_direction(direction, cd):
                if Logic.is_same_direction_by_two_point(last_cd, cd): 
                    if last_cd.high == last_cd.close and cd.open == cd.low and cd.open >= last_cd.close:
                        # 此处已经测试
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                    else:  
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.low, cd.high)
                else:
                    if last_cd.close > last_cd.low and cd.open == cd.low and cd.open >= last_cd.close:
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                    else:
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.low, cd.high)

            else:
                if Logic.is_same_direction_by_two_point(last_cd, cd):
                    if last_cd.close >= last_cd.low and cd.high >= cd.open and cd.open >= last_cd.close:
                        len = abs(cd.high - last_cd.low)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                        else:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
                    else:
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.open, cd.high)
                        else:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
                else:
                    if last_cd.high == last_cd.close and cd.high > cd.open and cd.open >= last_cd.close:
                        # 这里已经测试
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                    else:
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.open, cd.high)
                        else:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
        else:
            if QuotationLogic.is_same_direction(direction, cd):
                if Logic.is_same_direction_by_two_point(last_cd, cd):
                    if last_cd.close == last_cd.low and cd.open == cd.high and cd.open <= last_cd.close:
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)
                    else:
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.high, cd.low)
                else:
                    if last_cd.close < last_cd.high and cd.open == cd.high and cd.open <= last_cd.close:
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)
                    else:
                        max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.high, cd.low)
            else:
                if Logic.is_same_direction_by_two_point(last_cd, cd):
                    if last_cd.close <= last_cd.high and cd.open >= cd.low and cd.open <= last_cd.close:
                        len = abs(last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)                                                    
                        else:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
                    else:
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.open, cd.low) 
                        else:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
                else:
                    if last_cd.close == last_cd.low and cd.open > cd.low and last_cd.close >= cd.open:
                        len = abs(last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)
                        else:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
                    else:
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.open, cd.low) 
                        else:
                            max_l_to_d_obj = QuotationLogic.amplitude_obj(cd.high, cd.close) 

        # 记录下当前的max_l_to_d
        max_l_to_d_obj.datetime = cd.datetime
        return max_l_to_d_obj


    """
    分析统计最大的max_r
    """
    def get_max_r(direction, last_cd, cd): 
        if direction == Constants.DIRECTION_UP:
            if QuotationLogic.is_same_direction(direction, cd):
                if Logic.is_same_direction_by_two_point(last_cd, cd):
                    if  last_cd.close <= last_cd.high and cd.open >= cd.low and last_cd.close >= cd.open:
                        len = abs(last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)
                        else:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
                    else:
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.open, cd.low)
                        else:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
                else:
                    if last_cd.close == last_cd.low and cd.open > cd.low and last_cd.close >= cd.open:
                        len = abs(last_cd.high - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)
                        else:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
                    else:
                        len = abs(cd.open - cd.low)
                        end_len = abs(cd.high - cd.close)
                        if len > end_len:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.open, cd.low)
                        else:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.high, cd.close)
            else:
                if Logic.is_same_direction_by_two_point(last_cd, cd):
                    if last_cd.close == last_cd.low and cd.open == cd.high and last_cd.close >= cd.open:
                        max_r_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)
                    else:
                        max_r_obj = QuotationLogic.amplitude_obj(cd.high, cd.low)
                else:
                    if last_cd.high > last_cd.close and cd.open == cd.high and last_cd.close >= cd.open:
                        max_r_obj = QuotationLogic.amplitude_obj(last_cd.high, cd.low)
                    else:
                        max_r_obj = QuotationLogic.amplitude_obj(cd.high, cd.low)
        else:
            if QuotationLogic.is_same_direction(direction, cd):
                if Logic.is_same_direction_by_two_point(last_cd, cd):
                    if last_cd.close >= last_cd.low and cd.open <= cd.high and cd.open >= last_cd.close:
                        max_r_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                    else:
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.open, cd.high)
                        else:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
                else:
                    if last_cd.close == last_cd.high and cd.open < cd.high and cd.open >= last_cd.close:
                        len = abs(cd.high - last_cd.low)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_r_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                        else:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
                    else:
                        len = abs(cd.high - cd.open)
                        end_len = abs(cd.close - cd.low)
                        if len > end_len:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.open, cd.high)
                        else:
                            max_r_obj = QuotationLogic.amplitude_obj(cd.low, cd.close)
            else:
                if Logic.is_same_direction_by_two_point(last_cd, cd):
                    if last_cd.close == last_cd.high and cd.open == cd.high and cd.open >= last_cd.close:
                        max_r_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                    else:
                        # 已测试
                        max_r_obj = QuotationLogic.amplitude_obj(cd.low, cd.high)
                else:
                    if last_cd.close > last_cd.low and cd.open == cd.high and cd.open >= last_cd.close:
                        max_r_obj = QuotationLogic.amplitude_obj(last_cd.low, cd.high)
                    else:
                        max_r_obj = QuotationLogic.amplitude_obj(cd.low, cd.high)
        # 添加一个时间
        max_r_obj.datetime = cd.datetime

        return max_r_obj


    """
    设置当前的ir,比较 current_max_l_to_d_interval 跟 current_max_r的大小，大者为当前ir
    """
    def get_current_ir(direction, last_cd, cd):
        current_max_l_to_d_interval = QuotationLogic.get_max_l_to_d(direction, last_cd, cd)
        current_max_r = QuotationLogic.get_max_r(direction, last_cd, cd)
        if current_max_l_to_d_interval is not None and current_max_r is not None:
            if current_max_l_to_d_interval.length >= current_max_r.length:
                current_ir = current_max_l_to_d_interval
            else:
                current_ir = current_max_r
        elif current_max_l_to_d_interval is not None and current_max_r is None:
            current_ir = current_max_l_to_d_interval
        elif current_max_l_to_d_interval is None and current_max_r is not None:
            current_ir = current_max_r
        
        return current_ir

    
    """
    判断当前一分钟的方向是否跟主方向一致
    """
    def is_same_direction(direction, cd):
        if cd.direction == Constants.DIRECTION_UP and direction == Constants.DIRECTION_UP:
            return True
        elif cd.direction == Constants.DIRECTION_DOWN and direction == Constants.DIRECTION_DOWN:
            return True
        else:
            return False

    """
	设置长度跟开始点价格、结束点价格
	"""
    def amplitude_obj(start_price, end_price):
        obj = SimpleNamespace()
        obj.length = abs(start_price - end_price)
        obj.start_price = start_price
        obj.end_price = end_price
        if start_price < end_price:
            obj.direction = Constants.DIRECTION_UP
        elif start_price > end_price:
            obj.direction = Constants.DIRECTION_DOWN
        else:
            obj.direction = None

        return obj
    
    # 连续一个方向且反方向未突破连续方向，此时D无效，若上涨区间，直到下跌收盘价突破前一分钟低点出现有效极值D
    # capitalized 小写 uncapitalized
    def get_cr_information(cd, l, cr_obj = None):
        if len(l) == 0:
            if not Logic.is_crossing_starlike(cd):
                l = []
                l.append(cd)
                cr_obj = SimpleNamespace()
                if cd.direction == Constants.DIRECTION_UP:
                    cr_obj.start_price = cd.low
                    cr_obj.end_price = cd.high
                else:
                    cr_obj.start_price = cd.high
                    cr_obj.end_price = cd.low
                cr_obj.length = abs(cd.high - cd.low)
                cr_obj.direction = cd.direction

            return l, cr_obj
        
        first_cd = l[0]
        last_cd = l[-1]
        direction = first_cd.direction
        if direction == Constants.DIRECTION_UP:
            if cd.close < last_cd.low:
                return [], None
        else:
            if cd.close > last_cd.high:
                return [], None
        
        # 没有突破就加入
        l.append(cd)
        # 更新cr_obj 
        if direction == Constants.DIRECTION_UP:
            if cd.high > cr_obj.end_price:
                cr_obj.end_price = cd.high
                cr_obj.length = abs(cr_obj.start_price - cr_obj.end_price)
        else:
            if cd.low < cr_obj.end_price:
                cr_obj.end_price = cd.low
                cr_obj.length = abs(cr_obj.start_price - cr_obj.end_price)
        
        return l, cr_obj


    """
    在cr_obj转变后需要处理的初始最大ir,方向跟cr_obj一致
    """
    def get_max_ir_by_cr_list(l):
        if len(l) == 0:
            return None
        elif len(l) == 1:
            cd = l[0]
            if cd.direction == Constants.DIRECTION_UP:
                start_price = cd.low
                end_price = cd.high
                max_ir_by_cr = QuotationLogic.amplitude_obj(start_price, end_price)
                max_ir_by_cr.datetime = cd.datetime
            elif cd.direction == Constants.DIRECTION_DOWN:
                start_price = cd.high
                end_price = cd.low
                max_ir_by_cr = QuotationLogic.amplitude_obj(start_price, end_price)
                max_ir_by_cr.datetime = cd.datetime
            else:
                max_ir_by_cr = None
            return max_ir_by_cr
        else:
            l_len = len(l)
            max_ir_by_cr = None
            i = 0
            direction = l[0].direction
            max_ir_by_cr = None
            while i < (l_len-1):
                last_cd = l[i]
                cd = l[i+1]
                i += 1
                current_ir = QuotationLogic.get_current_ir(direction, last_cd, cd)
                if current_ir.direction == direction:
                    if max_ir_by_cr is None or (current_ir.length > max_ir_by_cr.length):
                        max_ir_by_cr = deepcopy(current_ir)
            return max_ir_by_cr

    """
    获取满足条件的价格
    """ 
    def get_last_price_by_cr_list(l, end_price, length):
        price = None
        first_cd = l[0]
        direction = first_cd.direction
        if direction == Constants.DIRECTION_UP:
            for cd in l:
                if abs(end_price - cd.low) > length and (cd.high <= end_price):
                    price = cd.low
        elif direction == Constants.DIRECTION_DOWN:
            for cd in l:
                if abs(end_price - cd.high) > length and (cd.low >= end_price):
                    price = cd.high
        
        return price


