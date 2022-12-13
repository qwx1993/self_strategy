from self_strategy.constants import Constants
from self_strategy.fake_break.logic import Logic
from copy import deepcopy
from types import SimpleNamespace

class Quotation:
    unit_value = 0 # 单位价格
    up_obj = None # 上涨对象
    up_interval_list = [] # 向上区间list
    up_continuous_obj = None # 向上连续对象

    down_obj = None # 下跌对象
    # temp_down_obj = None # 过渡期间使用的对象
    down_interval_list = [] # 向下区间list
    down_continuous_obj = None # 向下连续对象

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
        # 统计正向有效价格
        self.handle_up_effective_price(tick)
        # print(f"up_obj => {self.up_obj}")
        # 统计负向有效价格
        self.handle_down_effective_price(tick)
        # print(f"down_obj => {self.down_obj}")
        self.handle_effective_interval_list(tick)

        # 回到起点
        self.hanle_comeback_start(tick)

        self.handle_effective_continuous()

        # print(f"有效区间连续:up_continuous_obj => {self.up_continuous_obj} \ndown_continuous_obj => {self.down_continuous_obj}")

    """
    处理向上有效区间对象，如果低于起点则重置，如果高于终点就刷新终点跟长度
    """
    def handle_up_effective_price(self, tick):
        current = tick.current
        if current < self.up_obj.start:
            self.up_obj = Logic.get_base_obj(current, current)
        elif current > self.up_obj.end:
            self.up_obj = Logic.get_base_obj(self.up_obj.start, current)
    
    """
    处理向下有效区间对象，如果高于起点则重置，如果低于终点就刷新终点跟长度
    """
    def handle_down_effective_price(self, tick):
        current = tick.current
        if current > self.down_obj.start:
            self.down_obj = Logic.get_base_obj(current, current)
        elif current < self.down_obj.end:
            self.down_obj = Logic.get_base_obj(self.down_obj.start, current)
    
    """
    处理有效区间列表，当上下两个方向统计的长度都大于10单位时,长度较大的被打断写入到对应list中，并初始化统计值
    """
    def handle_effective_interval_list(self, tick):
        if self.up_obj.length >= 10*self.unit_value and self.down_obj.length >= 10*self.unit_value:
            if self.up_obj.length > self.down_obj.length:
                self.up_interval_list.append(self.up_obj)
                self.up_obj = Logic.get_base_obj(tick.current, tick.current)
                # print(f"up_interval_list => {self.up_interval_list}")
            elif self.up_obj.length < self.down_obj.length:
                self.down_interval_list.append(self.down_obj)
                self.down_obj = Logic.get_base_obj(tick.current, tick.current)
        
        # 判断临时对象是否会被覆盖
        up_interval_list_length = len(self.up_interval_list)
        if up_interval_list_length > 0:
            first_obj = self.up_interval_list[0]
            last_obj = self.up_interval_list[-1]
            if self.down_obj.end < last_obj.start:
                if up_interval_list_length == 1:
                    self.up_interval_list = []
                else:
                    self.up_interval_list = []
                    self.up_interval_list.append(first_obj)
        
        down_interval_list_length = len(self.down_interval_list)
        if down_interval_list_length > 0:
            first_obj = self.down_interval_list[0]
            last_obj = self.down_interval_list[-1]
            if self.up_obj.end > last_obj.start:
                if down_interval_list_length == 1:
                    self.down_interval_list = []
                else:
                    self.down_interval_list = []
                    self.down_interval_list.append(first_obj)

    """
    处理有效连续
    """     
    def handle_effective_continuous(self):
        # 正向价格连续
        if len(self.up_interval_list) >= 2:
            first_obj = self.up_interval_list[0]
            last_obj = self.up_interval_list[-1]

            if self.up_continuous_obj is None:
                self.up_continuous_obj = SimpleNamespace()
            self.up_continuous_obj.start = first_obj.start
            self.up_continuous_obj.end = last_obj.end
            self.up_continuous_obj.length = abs(first_obj.start - last_obj.end)
        else:
            self.up_continuous_obj = None
        
        if len(self.down_interval_list) >= 2:
            first_obj = self.down_interval_list[0]
            last_obj = self.down_interval_list[-1]
            if self.down_continuous_obj is None:
                self.down_continuous_obj = SimpleNamespace()
            self.down_continuous_obj.start = first_obj.start
            self.down_continuous_obj.end = last_obj.end
            self.down_continuous_obj.length = abs(first_obj.start - last_obj.end)
        else:
            self.down_continuous_obj = None
    
    """
    回到起点时去掉区间list
    """
    def hanle_comeback_start(self, tick):
        if len(self.up_interval_list) > 0:
            first_cd = self.up_interval_list[0]
            if tick.current < first_cd.start:
                self.up_interval_list = []
        
        if len(self.down_interval_list) > 0:
            down_first_cd = self.down_interval_list[0]
            if tick.current > down_first_cd.start:
                self.down_interval_list = []
