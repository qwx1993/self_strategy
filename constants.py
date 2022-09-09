class Constants:
    # 米筐用户名
    RQDATA_USERNAME = 'license'
    # 米筐账户密码token
    RQDATA_PASSWORD = 'ioy7idT7M-0_UjoQaFGKuJOQxdSS7qWLTWW6IRcutIvZuHWxgfoJ7lxQblmhG2G31Vnrnk6QwjjIB3W36L3OqtEJqaPviE98-c-slvEwX0Cr-4pDwPee1omGjHIy29jkJmzZ6eQNmLO9CLBDLn8JO6dbMoUEmWnVz98U9MTuu18=C6KPKOUYUmbNtg_4ci5iIQmOi_O0vn8hd0v-VlJXUJVbSiUlV8tk_MmCRT8pRWvAVtS6CtofFrH4DuLZQAwgbxQGhnFCXxdrg3iTquW-zvODJjUXek63KGnYQgYetB_jUGfoN_uNoPvEFTzLiphnSxzSaYqW-t4trJb22hU5ZNA='

    STRATEGIES_DATA_PATH = 'C:/Users/Administrator/strategies/data/' # 数据分析的文件保存地址  
     
    OSCILLATING_INTERVAL_POINT_NUMBER = 3  # 振荡区间高点数B1
    MULTIPLE_OF_BREAKTHROUGH = 5 # D突破振荡区间后的价格D1大于振荡区间5倍

    # 用来判断上涨加速阶段或下跌加速阶段的时间单位长度，包括加速之前的若干参考波动的时间单位和加速上涨/下跌本身的时间单位长度
    REFERENCE_AND_SPEEDING_LENGTH = 50000
    AVG_FLUNC_LENGTH = 10  # 加速上涨/下跌之前参考平均波动的时间单位长度
    AVG_MULTIPLIER = 3  # 参考平均波动的倍数
    # 当天开盘的第一分钟的开盘价已经大于（前一天最后10分钟平均波动的3倍+前一天最后的收盘价），并且开盘的第一分钟是上涨的，则算作3次宽幅上涨
    POSSIBLE_SPEEDING_0 = 1
    POSSIBLE_SPEEDING_1 = 3  # 加速上涨/下跌的可能时间长度1
    POSSIBLE_SPEEDING_2 = 4  # 加速上涨/下跌的可能时间长度2
    POSSIBLE_SPEEDING_3 = 5  # 加速上涨/下跌的可能时间长度3
    # 此处为默认值，加速上涨后最多多少分钟内要发生开空动作，否则废除掉这次加速上涨/下跌
    DEFAULT_TIME_LIMIT_AFTER_RISE_SPEEDING = 3
    DEFAULT_TIME_LIMIT_AFTER_FALL_SPEEDING = 10  # 此处为默认值，加速下跌完成后的时间限制
    DEFAULT_TIME_TO_IMMEDIATE_CLOSE_SHORT = 2

    DIRECTION_UP = 1 # 向上
    DIRECTION_NONE = 0 # 无方向
    DIRECTION_DOWN = -1 # 向下

    # 新的状态集
    STATUS_NONE = -1
    STATUS_FIND_D1 = 0
    NON_ACCELERATING_OSCILLATION = 1  # 非加速振荡

    TICK_STATUS_NONE = -1
    TICK_STATUS_FIND_D1 = 0
    TICK_STATUS_STATISTIC = 1  # 非加速振荡
    TICK_STATUS_PAUSE = 2 # 停止状态
    
    OSCILLATION_PROCESS_TYPE_TO_L = 0  # d to l
    OSCILLATION_PROCESS_TYPE_TO_D = 1  # l to d

    DIRECTION_TYPE_OF_D_TO_L = 1  # 以顺趋势为例，从D到L的过程
    DIRECTION_TYPE_OF_L_TO_D = -1  # 以顺趋势为例，从L到D的过程

    SUB_STATUS_OF_L1 = 300  # 寻找l1
    SUB_STATUS_OF_D2 = 301  # 寻找d2点，根据d2的情况判断是情况一还是情况二，或者重开
    STOP_SURPLUS_OR_LOSS_SITUATION_ONE = 302  # 情况一止盈或止损
    STOP_SURPLUS_OR_LOSS_SITUATION_TWO = 303 # 情况二止盈或止损
    STOP_SURPLUS_FINISH = 304 # 止盈完成后，出现Ln的低点比dn_to_ln_max低就判断是否存在逆趋势，否则进入新的循环
    SITUATION_TWO = 305  # 情况二
    SITUATION_TWO_WAIT_OPEN_A_POSITION = 306  # 情况二开仓
    COUNTER_TREND = 307  # 逆趋势
    COUNTER_TREND_CLOSE_A_POSITION = 308  # 平仓

    SITUATION_ONE_STATUS_OF_D2 = 350  # 寻找D2点，出现D2 > D1 就开仓
    SITUATION_ONE_STATUS_OF_STOP_SURPLUS_OR_LOSS = 351  # 情况一止盈或者止损
    SITUATION_ONE_REVERSE_OPEN_A_POSITION = 352  # 情况一进入逆趋势开仓
    SITUATION_ONE_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH = 353  # 情况一止盈或止损状态
    SITUATION_ONE_STATUS_OF_CLOSE = 354 # 在逆趋势出现后，振荡次数比之前大就进入这个状态
    # 情况二
    SITUATION_TWO_STATUS_OF_D2 = 360
    SITUATION_TWO_STATUS_OF_WAIT_OPEN_A_POSITION = 361
    SITUATION_TWO_STATUS_OF_STOP_SURPLUS_OR_LOSS = 362
    SITUATION_TWO_REVERSE_OPEN_A_POSITION = 363
    SITUATION_TWO_STATUS_OF_STOP_SURPLUS_OR_LOSS_FINISH = 364
    SITUATION_TWO_STATUS_OF_CLOSE = 365  # 在逆趋势出现后，振荡次数比之前大就进入这个状态

    ACTIONS_INDEX_DEFAULT = 0 # 逆趋势
    ACTIONS_INDEX_ONE = 1 # 情况一
    ACTIONS_INDEX_TWO = 2 # 情况二

    # 是否在逆趋势中
    STATUS_COUNTER_TREND_NO = 0  # 非逆趋势状态中
    STATUS_COUNTER_TREND_YES = 1  # 逆趋势状态中

    # 是否在逆趋势中
    NEED_CHECK_OSCILLATION_STATUS_NO = 0  # 不需要检测振荡
    NEED_CHECK_OSCILLATION_STATUS_YES = 1  # 需要检测振荡

    ACTION_OPEN_SHORT = 201  # 开空动作
    ACTION_CLOSE_SHORT = 202  # 平空动作

    ACTION_REVERSE_OPEN_SHORT = 203  # 逆趋势开空
    ACTION_REVERSE_CLOSE_SHORT = 204  # 逆趋势平空

    ACTION_OPEN_LONG = 205  # 开多动作
    ACTION_CLOSE_LONG = 206  # 平多动作

    ACTION_REVERSE_OPEN_LONG = 207  # 逆趋势开多
    ACTION_REVERSE_CLOSE_LONG = 208  # 逆趋势平多

    OPEN_A_POSITION_ONE_LONG = 0  # 情况一开多
    OPEN_A_POSITION_ONE_SHORT = 1  # 情况一开空
    OPEN_A_POSITION_TWO_LONG = 2  # 情况二开多
    OPEN_A_POSITION_TWO_SHORT = 3  # 情况二开空
    STOP_SURPLUS_ONE = 4  # 情况一止盈
    STOP_SURPLUS_TWO = 5  # 情况二止盈
    STOP_LOSS_ONE = 6  # 情况一止损
    STOP_LOSS_TWO = 7  # 情况二止损
    REVERSE_OPEN_A_POSITION_ONE_LONG = 8  # 逆一开多
    REVERSE_OPEN_A_POSITION_ONE_SHORT = 9  # 逆一开空
    REVERSE_OPEN_A_POSITION_TWO_LONG = 10  # 逆二开多
    REVERSE_OPEN_A_POSITION_TWO_SHORT = 11  # 逆二开空
    REVERSE_STOP_SURPLUS_ONE = 12  # 逆一止盈
    REVERSE_STOP_SURPLUS_TWO = 13  # 逆二止盈
    REVERSE_STOP_LOSS_ONE = 14  # 逆一止损
    REVERSE_STOP_LOSS_TWO = 15  # 逆二止损
    INDEX_DAY_CLOSE = 16  # 当日收盘平仓
    INDEX_OBSERVE = 17
    INDEX_B1_LINE = 18  # 画b1辅助线
    INDEX_COUNTER_TREND_SHORT = 19  # 逆趋势开空
    INDEX_COUNTER_TREND_LONG = 20  # 逆趋势开多
    INDEX_COUNTER_TREND_CLOSE_A_POSITION = 21  # 逆趋势平仓


    HISTORY_STATUS_OF_NONE = 0 # 初始状态
    HISTORY_STATUS_OF_TREND = 1 # 趋势中状态


    STR_ACTIONS_AND_STATES = {
        OPEN_A_POSITION_ONE_LONG: {
            "cn": "情况一开多",
            "en": "open a position one long",
        },
        OPEN_A_POSITION_ONE_SHORT: {
            "cn": "情况一开空",
            "en": "open a position one short",
        },
        OPEN_A_POSITION_TWO_LONG: {
            "cn": "情况二开多",
            "en": " open a position two long"
        },
        OPEN_A_POSITION_TWO_SHORT: {
            "cn": "情况二开空",
            "en": " open a position two short"
        },
        STOP_SURPLUS_ONE: {
            "cn": "情况一止盈",
            "en": "stop surplus one",
        },
        STOP_SURPLUS_TWO: {
            "cn": "情况二止盈",
            "en": "stop surplus two",
        },
        STOP_LOSS_ONE: {
            "cn": "情况一止损",
            "en": "stop loss one"
        },
        STOP_LOSS_TWO: {
            "cn": "情况二止损",
            "en": "stop loss two"
        },
        REVERSE_OPEN_A_POSITION_ONE_LONG: {
            "cn": "逆-情况一开多",
            "en": "reverse open a position one long",
        },
        REVERSE_OPEN_A_POSITION_ONE_SHORT: {
            "cn": "逆-情况一开空",
            "en": "reverse open a position one short",
        },
        REVERSE_OPEN_A_POSITION_TWO_LONG: {
            "cn": "逆-情况二开多",
            "en": "reverse open a position two long",
        },
        REVERSE_OPEN_A_POSITION_TWO_SHORT: {
            "cn": "逆-情况二开空",
            "en": "reverse open a position two short",
        },
        REVERSE_STOP_SURPLUS_ONE: {
            "cn": "逆-情况一止盈",
            "en": "reverse stop surplus one",
        },
        REVERSE_STOP_SURPLUS_TWO: {
            "cn": "逆-情况二止盈",
            "en": "reverse stop surplus two",
        },
        REVERSE_STOP_LOSS_ONE: {
            "cn": "逆-情况一止损",
            "en": "reverse stop loss one"
        },
        REVERSE_STOP_LOSS_TWO: {
            "cn": "逆-情况二止损",
            "en": "reverse stop loss two"
        },
        INDEX_OBSERVE: {
            "cn": "c",
            "en": "c",
        },
        INDEX_DAY_CLOSE: {
            "cn": "当日收盘平仓",
            "en": "last_minute_close_future",
        },
        INDEX_B1_LINE: {
            "cn": "b1",
            "en": "b1"
        },
        INDEX_COUNTER_TREND_SHORT: {
            "cn": "逆-开空",
            "en": "counter trend short",
        },
        INDEX_COUNTER_TREND_LONG: {
            "cn": "逆-开多",
            "en": "counter trend long",
        },
        INDEX_COUNTER_TREND_CLOSE_A_POSITION: {
            "cn": "逆趋势平仓",
            "en": "counter trend",
        }
    }
