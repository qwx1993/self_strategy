from operator import truediv
import sys
from self_strategy.constants import Constants

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
