from types import SimpleNamespace
import os
import copy
from datetime import datetime
from datetime import timedelta
from self_strategy.constants import Constants
from self_strategy.logic import Logic

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
