from operator import truediv
import sys
from self_strategy.constants import Constants
from self_strategy.logic import Logic

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
    def open_a_price_by_agreement_cr(direction, effective_ir, tick):
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

        if trade_action == Constants.ACTION_CLOSE_LONG:
            if tick.current < close_price:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if tick.current > close_price:
                return True
        return False
