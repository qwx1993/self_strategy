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
    通过tick进行平仓
    """
    def close_a_price(trade_action, last_cd, tick):

        if trade_action == Constants.ACTION_CLOSE_LONG:
            if tick.current < last_cd.low:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if tick.current > last_cd.high:
                return True
        return False
