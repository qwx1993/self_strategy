from operator import truediv
import sys
from self_strategy.constants import Constants
from self_strategy.logic import Logic
from self_strategy.quotation_logic import QuotationLogic

class Tick:

    """
    通过tick进行开仓
    """ 
    def open_a_price(direction, last_cd, tick):
        if direction == Constants.DIRECTION_UP:
            if tick.current > last_cd.high:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if tick.current < last_cd.low:
                return True
        return False
    
    """
    通过指定开仓价进行开仓
    """
    def open_a_position_by_price(direction, price, tick):
        if direction == Constants.DIRECTION_UP:
            if tick.current > price:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if tick.current < price:
                return True
        return False
    """
    方向向上时，在接下来的一分钟内低于协定d的价格开仓
    方向向下时，在接下来的一分钟内高于协定d的价格开仓
    """
    def open_a_price_by_agreement(direction, extremum_d, agreement_extremum_d, last_cd, tick):
        if extremum_d is None or agreement_extremum_d is None:
            return False
        # 如果协定D的tag是false就不开仓
        if not agreement_extremum_d.tag:
            return False

        # if direction == Constants.DIRECTION_UP:
        #     if tick.current >= last_cd.low:
        #         return False
        # elif direction == Constants.DIRECTION_DOWN:
        #     if tick.current <= last_cd.high:
        #         return False
        # todo 等下可以简化
        # if not Logic.within_minutes(30, extremum_d.datetime, agreement_extremum_d.datetime):
        if direction == Constants.DIRECTION_UP:
            if tick.current < agreement_extremum_d.open_price:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if tick.current > agreement_extremum_d.open_price:
                return True
        
        return False

    """
    方向向上时，在接下来的一分钟内低于协定d的价格开仓
    方向向下时，在接下来的一分钟内高于协定d的价格开仓
    """
    def open_a_price_by_agreement_cr(direction, agreement_cr_obj, effective_ir, tick):
        if agreement_cr_obj is None or (not agreement_cr_obj.tag):
            return False

        if effective_ir is None:
            return False

        if direction == Constants.DIRECTION_UP:
            if tick.current < effective_ir.low:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if tick.current > effective_ir.high:
                return True
        
        return False
    
    """
    方向向上，tick的价格比协议ir的起点价低开仓
    方向向下，tick的价格比协议ir的起点价高开仓
    """
    def open_a_price_by_agreement_ir(direction, agreement_ir, tick):
        if agreement_ir is None or (not agreement_ir.tag):
            return False
        
        if direction == Constants.DIRECTION_UP:
            if tick.current < agreement_ir.start_price:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if tick.current > agreement_ir.start_price:
                return True
        return False
    
    
    """
    有效突破的IRlast（IR>10）被Cr覆盖后，出现Tick突破有效D且IR＜IRlast（IR>10），Tick回归且Ir>10视为有效回归
    """
    def open_a_price_by_effective_regression(direction, effective_d, effective_ir_last, current_ir, cd, unit_value):
        if effective_d is None or effective_ir_last is None or current_ir is None  or cd is None:
            return False

        # 非无效突破不开仓
        if not effective_d.bk_type == Constants.BK_TYPE_OF_INEFFECTIVE:
            return False
        
        if not effective_d.tag:
            return False

        # 当前ir跟主方向一致不开仓
        if direction == current_ir.direction:
            return False
        # 当前current_ir的长度比有效ir_last的长度大结束,或者小于10结束
        if current_ir.length > effective_ir_last.length or current_ir.length < 10*unit_value:
            return False

        if direction == Constants.DIRECTION_UP:
            if current_ir.start_price > effective_d.low > current_ir.end_price:
                if cd.close < effective_d.low:
                    return True
        elif direction == Constants.DIRECTION_DOWN:
            if current_ir.end_price > effective_d.high > current_ir.start_price:
                if cd.close > effective_d.high:
                    return True
        
        return False
    
    """
    方向向上时，在接下来的一分钟内高于协定l的价格开仓
    方向向下时，在接下来的一分钟内低于协定l的价格开仓
    """
    def open_a_price_by_agreement_l(direction, extremum_l, h_price, last_cd, tick):
        if extremum_l is None or h_price is None:
            return False

        # if direction == Constants.DIRECTION_UP:
        #     if tick.current >= last_cd.low:
        #         return False
        # elif direction == Constants.DIRECTION_DOWN:
        #     if tick.current <= last_cd.high:
        #         return False
    
        if direction == Constants.DIRECTION_UP:
            if tick.current < extremum_l.low:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if tick.current > extremum_l.high:
                return True
        return False
    
    """
    通过tick进行开仓
    """ 
    def open_a_price_by_l_start_cd(direction, start_cd, minute_cd, l_price, tick):
        if start_cd is None or l_price is None:
            return False

        if direction == Constants.DIRECTION_UP:
            if (start_cd.price == l_price == minute_cd.low) and tick.current >= start_cd.price:
                return True
            elif (start_cd.price > minute_cd.low >= l_price) and tick.current >= start_cd.price:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if (start_cd.price == minute_cd.high == l_price) and tick.current <= start_cd.price:
                return True
            elif (start_cd.price < minute_cd.high <= l_price) and tick.current <= start_cd.price:
                return True
        return False
    
    """
    通过tick进行开仓
    """ 
    def open_a_price_by_h_start_cd(direction, h_start_cd, minute_cd, h_price, tick):
        if h_start_cd is None or h_price is None:
            return False
        if direction == Constants.DIRECTION_UP:
            if (h_start_cd.price == minute_cd.high == h_price) and tick.current <= h_start_cd.price:
                return True
            elif (h_start_cd.price < minute_cd.high <= h_price) and tick.current <= h_start_cd.price:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if (h_start_cd.price == h_price == minute_cd.low) and tick.current >= h_start_cd.price:
                return True
            elif (h_start_cd.price > minute_cd.low >= h_price) and tick.current >= h_start_cd.price:
                return True
        return False
    
    """
    通过tick进行平仓
    """
    def close_a_price(trade_action, close_price, tick):
        if close_price is None:
            return False

        if trade_action == Constants.ACTION_CLOSE_LONG:
            if tick.current < close_price:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if tick.current > close_price:
                return True
        return False


    """
    通过收盘价进行平仓
    """
    def close_a_price_by_cd(trade_action, close_price, cd):
        if close_price is None:
            return False

        if trade_action == Constants.ACTION_CLOSE_LONG:
            if cd.close < close_price:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if cd.close > close_price:
                return True
        return False

    """
    平仓通过有效突破时间
    """
    def close_a_price_by_effective_breakthrough(breakthrough_datetime, cd):
        if breakthrough_datetime == cd.datetime:
            return True
        return False

    """
    Tick>10突破最近的Ir>10
    """
    def close_a_price_by_breakthrough_ir_last(trade_action, current_ir, ir_last, unit_value):
        if current_ir is None or ir_last is None:
            return False

        if current_ir.direction == ir_last.direction:
            return False
        
        if current_ir.length < 10*unit_value:
            return False
        
        if trade_action == Constants.ACTION_CLOSE_LONG:
            if current_ir.end_price < ir_last.start_price:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if current_ir.end_price > ir_last.start_price:
                return True
        return False


