import os
from datetime import datetime
from datetime import timedelta



"""
是否需要平仓
"""
def need_close_position(vt_symbol):
    vt_symbol = vt_symbol.upper()
    now_date = datetime.now()
    hour = now_date.hour
    minute = now_date.minute
    # 23点平仓
    twenty_three_list = [
        'A2211.DCE',
        'B2211.DCE',
        'BU2212.SHFE',
        'C2301.DCE',
        'CS2211.DCE',
        'EB2212.DCE',
        'EG2301.DCE',
        'FG301.CZCE',
        'FU2301.SHFE',
        'HC2301.SHFE',
        'I2301.DCE',
        'J2301.DCE',
        'JM2301.DCE',
        'L2301.DCE',
        'LU2301.INE',
        'M2301.DCE',
        'MA301.CZCE',
        'P2301.DCE',
        'PP2301.DCE',
        'RB2301.SHFE',
        'RM301.CZCE',
        'RU2301.SHFE',
        'SA301.CZCE',
        'SP2301.SHFE',
        'SR301.CZCE',
        'TA301.CZCE',
        'V2301.DCE',
        'Y2301.DCE',
        'EB2212.DCE',     
        'PG2211.DCE',
    ]
    # 01 点平仓
    one_list = [
        'AL2211.SHFE',
        'AU2212.SHFE',
        'BC2212.INE',
        'CU2211.SHFE',
        'NI2211.SHFE',
        'PB2211.SHFE',
        'SN2211.SHFE',
        'SS2211.SHFE',
        'ZN2211.SHFE',
    ]

    # 02：30
    half_past_two_list = [
        'AG2212.SHFE',
        'SC2211.INE',
    ]
        # 两点之后平仓
    if hour == 14 and minute >= 55:
        return True

    if vt_symbol in twenty_three_list:
        if hour == 22 and minute >= 55:
            return True 
    elif vt_symbol in one_list:
        if hour == 0 and minute >= 55:
            return True
    elif vt_symbol in half_past_two_list:
        if hour == 1 and minute >= 25:
            return True
    return False

"""
可以开仓时间
"""
def can_open_a_position(vt_symbol):
    return not need_close_position(vt_symbol)
