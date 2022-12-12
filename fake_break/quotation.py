from self_strategy.constants import Constants
from self_strategy.fake_break.logic import Logic

class Quotation:
    unit_value = 0 #单位价格
    up_obj = None # 上涨对象
    down_obj = None # 下跌对象
    status = Constants.HISTORY_STATUS_OF_NONE # 状态，初始化起点状态，行情状态
    last_cd = None

    def __init__(self, unit_value) -> None:
        self.unit_value = unit_value
        self.up_obj = None
        self.down_obj = None

    def analysis(self, tick):
        if self.status == Constants.HISTORY_STATUS_OF_NONE: 
            self.handle_status_none(tick)
        elif self.status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
            self.statistic(tick)

        self.last_cd = tick

    """
    初始统计相关参数
    """
    def handle_status_none(self, tick):
        self.up_obj = Logic.get_base_obj(tick.current, tick.current)
        self.down_obj = Logic.get_base_obj(tick.current, tick.current)  
        self.last_cd = tick
        self.set_status(Constants.HISTORY_STATUS_OF_TREND)
    
    """
    设置状态
    """
    def set_status(self, status):
        self.status = status
    

    """
    分析行情数据
    """
    def statistic(self, tick):
        self.handle_up_logic(tick)
        print(f"up_obj => {self.up_obj}")
        self.handle_down_logic(tick)
        print(f"down_obj => {self.down_obj}")
        pass

    """
    处理向上有效区间对象，如果低于起点则重置，如果高于终点就刷新终点跟长度
    """
    def handle_up_logic(self, tick):
        current = tick.current
        if current < self.up_obj.start:
            self.up_obj = Logic.get_base_obj(current, current)
        elif current > self.up_obj.end:
            self.up_obj = Logic.get_base_obj(self.up_obj.start, current)
    
    """
    处理向下有效区间对象，如果高于起点则重置，如果低于终点就刷新终点跟长度
    """
    def handle_down_logic(self, tick):
        current = tick.current
        if current > self.down_obj.start:
            self.down_obj = Logic.get_base_obj(current, current)
        elif current < self.down_obj.end:
            self.down_obj = Logic.get_base_obj(self.down_obj.start, current)
