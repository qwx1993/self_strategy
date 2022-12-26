class Constants:
    EFFECTIVE_STATUS_OF_DOWN = 'down' # 向上
    EFFECTIVE_STATUS_OF_UP = 'up' # 向下
    EFFECTIVE_STATUS_OF_NONE = None # 无状态

    CONTINUOUS_STATUS_OF_NONE = None # 连续状态
    CONTINUOUS_STATUS_OF_DOWN = 'down' # 向下连续状态
    CONTINUOUS_STATUS_OF_UP = 'up' # 向上连续状态

    MOVE_EFFECTIVE_STATUS_OF_NONE = None # 运动有效状态
    MOVE_EFFECTIVE_STATUS_OF_DOWN = 'down' # 向下的有效状态
    MOVE_EFFECTIVE_STATUS_OF_UP = 'up' # 向上的有效状态

    INVERSE_STATS_OF_NONE = 0 # 默认状态
    INVERSE_STATUS_OF_INIT = 1 # 初始进入状态
    INVERSE_STATS_OF_BACK = 2 # 回调状态

