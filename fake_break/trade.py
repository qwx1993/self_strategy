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
        elif direction == Constants.DIRECTION_DOWN and effective_status == FBCons.EFFECTIVE_STATUS_OF_UP:
            if tick.current > last_obj.start:
                return True

        return False
    
    """
    在有效趋势向上时，如果终点下移就开仓
    有效趋势向下时，终点上移就平仓
    """
    def open_a_price_by_list(trend_obj, interval_list, effective_status):
        if trend_obj is None:
            return False
        
        if len(interval_list) < 2:
            return False

        direction = trend_obj.direction

        last_obj = interval_list[-1]
        second_last_obj = interval_list[-2]

        if direction == Constants.DIRECTION_UP:
            if last_obj.end < second_last_obj.end and effective_status == FBCons.EFFECTIVE_STATUS_OF_DOWN:
                return True
        elif direction == Constants.DIRECTION_DOWN and effective_status == FBCons.EFFECTIVE_STATUS_OF_UP:
            if last_obj.end > second_last_obj.end:
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
    
    """
    开空情况下，向下方向的终点上移动就平仓
    开多情况下，向上方向的终点下移就平仓
    """
    def close_a_price_by_list(trade_action, effective_status, interval_list):
        if len(interval_list) < 2:
            return False

        if trade_action == Constants.ACTION_CLOSE_LONG:
            if effective_status == FBCons.EFFECTIVE_STATUS_OF_DOWN:
                first_obj = interval_list[-2]
                last_obj = interval_list[-1]
                if last_obj.end < first_obj.end:
                    return True
        elif trade_action == Constants.ACTION_CLOSE_SHORT:
            if effective_status == FBCons.EFFECTIVE_STATUS_OF_UP:
                first_obj = interval_list[-2]
                last_obj = interval_list[-1]
                if last_obj.end > first_obj.end:
                    return True
        return False