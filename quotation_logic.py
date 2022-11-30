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

    # def get_cr_obj()

        
        # if not Logic.is_crossing_starlike(cd):
        #     if len(self.cr_list) == 0:
        #         self.cr_list.append(cd)
        #         # print(f"将开盘的幅度统计进去 {self.cr_list} yesterday_close_price => {self.yesterday_close_price} => cd => {cd}")
        #     elif len(self.cr_list) > 0:
        #         temp_last_cd = self.cr_list[-1]
        #         if not cd.direction == temp_last_cd.direction:
        #             self.cr_list = []
        #             # 重置ir
        #             self.max_ir_by_cr = None 
        #         self.cr_list.append(cd)
            
        #     if len(self.cr_list) > 0:
        #         temp_start_cd = self.cr_list[0]
        #         temp_end_cd = self.cr_list[-1]
        #         temp_direciton = temp_start_cd.direction
        #         if self.cr_obj is None:
        #             self.cr_obj = SimpleNamespace()
        #         if temp_direciton == Constants.DIRECTION_UP:
        #             self.cr_obj.start_price = temp_start_cd.low
        #             self.cr_obj.end_price = temp_end_cd.high
        #             self.cr_obj.length = abs(temp_end_cd.high - temp_start_cd.low)
        #             self.cr_obj.direction = temp_direciton
        #         elif temp_direciton == Constants.DIRECTION_DOWN:
        #             self.cr_obj.start_price = temp_start_cd.high
        #             self.cr_obj.end_price = temp_end_cd.low
        #             self.cr_obj.length = abs(temp_start_cd.high - temp_end_cd.low)
        #             self.cr_obj.direction = temp_direciton
        #         if self.cr_obj is not None and (self.max_cr_obj is None or self.cr_obj.length > self.max_cr_obj.length):
        #             self.max_cr_obj = deepcopy(self.cr_obj)
        #             self.max_cr_list = deepcopy(self.cr_list)
