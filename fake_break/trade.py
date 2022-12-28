from operator import truediv
import sys
from self_strategy.constants import Constants
from self_strategy.logic import Logic
from self_strategy.quotation_logic import QuotationLogic
from self_strategy.fake_break.constants import Constants as FBCons

class Trade:

    """
    通过tick进行开仓
    """ 
    def open_a_price(trend_obj, last_obj, effective_status, tick):
        if trend_obj is None or last_obj is None:
            return False

        if not trend_obj.end == last_obj.end:
            return False

        direction = trend_obj.direction

        if direction == Constants.DIRECTION_UP:
            if tick.current < last_obj.start and effective_status == FBCons.EFFECTIVE_STATUS_OF_DOWN:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if tick.current > last_obj.start and effective_status == FBCons.EFFECTIVE_STATUS_OF_UP:
                return True

        return False
    
    """
    通过tick进行平仓
    """
    def close_a_price(trade_action, continouns_status):
        if trade_action == Constants.ACTION_CLOSE_LONG:
            if continouns_status == FBCons.CONTINUOUS_STATUS_OF_DOWN:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if continouns_status == FBCons.CONTINUOUS_STATUS_OF_UP:
                return True

        return False
    
    def close_by_length(trade_action, effective_status):
        if trade_action == Constants.ACTION_CLOSE_LONG:
            if effective_status == FBCons.EFFECTIVE_STATUS_OF_DOWN:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if effective_status == FBCons.EFFECTIVE_STATUS_OF_UP:
                return True
        return False

    
    """
    通过指定价格进行止损
    """
    def close_by_appoint_price(trade_action, price, tick):
        if trade_action == Constants.ACTION_CLOSE_LONG:
            if tick.current < price:
                return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if tick.current > price:
                return True
        return False