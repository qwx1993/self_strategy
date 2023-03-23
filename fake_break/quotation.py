from self_strategy.constants import Constants
from self_strategy.fake_break.logic import Logic
from copy import deepcopy
from types import SimpleNamespace
from self_strategy.fake_break.constants import Constants as FKCons
import sys
from self_strategy.logic import Logic as SLogic
from self_strategy.utils import (
    file,
)

class Quotation:
    unit_value = 0 # 单位价格
    up_obj = None # 上涨对象
    up_interval_list = [] # 向上区间list
    up_continuous_obj = None # 向上连续对象
    last_up_obj = None # 最后向上的对象


    down_obj = None # 下跌对象
    # temp_down_obj = None # 过渡期间使用的对象
    down_interval_list = [] # 向下区间list
    down_continuous_obj = None # 向下连续对象
    last_down_obj = None # 最后的下跌对象
    last_down_interval_list = [] # 统计为最后向下的两个区间

    status = Constants.HISTORY_STATUS_OF_NONE # 状态，初始化起点状态，行情状态
    last_cd = None
    effective_status = FKCons.EFFECTIVE_STATUS_OF_NONE # 有效价格状态
    effective_move_status = FKCons.MOVE_EFFECTIVE_STATUS_OF_NONE # 有效运动状态
    continouns_status = FKCons.CONTINUOUS_STATUS_OF_NONE # 连续状态
    
    effective_trend_obj = None # 有效趋势对象
    interval_length = None # 有效价格间隔长度
    effective_trend_length = None

    log_obj = None


    def __init__(self, unit_value, interval_length, effective_trend_length) -> None:
        self.unit_value = unit_value
        self.up_obj = None
        self.down_obj = None
        self.log_obj = file.get_logger(f"quotation_{interval_length}")
        self.interval_length = interval_length*unit_value
        self.effective_trend_length = effective_trend_length*unit_value

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

        # 统计负向有效价格
        self.handle_down_effective_price(tick)

        # 初始化有效状态
        self.init_effective_status()

        # 有效区间
        self.handle_effective_interval_list(tick)

        # 统计有效连续 有效运动
        self.handle_effective_move()

        # 反向有效价格区间
        self.handle_effective_reverse()

        # 反向有效运动
        self.hanle_reverse_effective_move()

        self.handle_effective_trend(tick)

    """
    处理向上有效区间对象，如果低于起点则重置，如果高于终点就刷新终点跟长度
    """
    def handle_up_effective_price(self, tick):
        self.last_up_obj = deepcopy(self.up_obj)
        current = tick.current
        if current < self.up_obj.start:
            self.up_obj = Logic.get_base_obj(current, current)
        elif current > self.up_obj.end:
            self.up_obj = Logic.refresh_base_obj(self.up_obj, current)
        
    
    """
    处理向下有效区间对象，如果高于起点则重置，如果低于终点就刷新终点跟长度
    """
    def handle_down_effective_price(self, tick):
        self.last_down_obj = deepcopy(self.down_obj)
        current = tick.current
        if current > self.down_obj.start:
            self.down_obj = Logic.get_base_obj(current, current)
        elif current < self.down_obj.end:
            self.down_obj = Logic.refresh_base_obj(self.down_obj, current)
    
    """
    初始化主程序的有效方向
    依据最先达到有效价格定方向，当向上对象先达到，初始化有效状态为向上，当向下对象先达到，初始化有效状态为向下
    """
    def init_effective_status(self):
        if self.effective_status == FKCons.EFFECTIVE_STATUS_OF_NONE:
            if self.up_obj.length >= self.interval_length:
                self.effective_status = FKCons.EFFECTIVE_STATUS_OF_UP
            elif self.down_obj.length >= self.interval_length:
                self.effective_status = FKCons.EFFECTIVE_STATUS_OF_DOWN
    
    """
    当有效状态向上时，此时如果向下对象长度达到有效价格长度，将最后的向上对象写入到向上区间列表，并重置向上对象
    当有效状态向下时，此时如果向上对象长度达到有效价格长度，将最后的向下对象写入到向下区间列表，并重置向下对象
    """
    def handle_effective_interval_list(self, tick):
        if self.effective_status == FKCons.EFFECTIVE_STATUS_OF_UP:
            if self.down_obj.length >= self.interval_length:
                self.log_obj.info(f"up => {self.last_up_obj}")
                self.init_continuous_status(FKCons.CONTINUOUS_STATUS_OF_UP)
                if self.last_up_obj is not None and self.continouns_status == FKCons.CONTINUOUS_STATUS_OF_UP:
                    # self.up_interval_list.append(self.last_up_obj)
                    self.up_interval_list = Logic.append(self.up_interval_list, self.last_up_obj)
                self.up_obj = Logic.get_base_obj(tick.current, tick.current)
                self.onchange_effective_status(FKCons.EFFECTIVE_STATUS_OF_DOWN)
        elif self.effective_status == FKCons.EFFECTIVE_STATUS_OF_DOWN:
            if self.up_obj.length >= self.interval_length:
                self.log_obj.info(f"down => {self.last_down_obj}")
                self.last_down_interval_list = Logic.append_last(self.last_down_interval_list, self.last_down_obj)
                self.init_continuous_status(FKCons.CONTINUOUS_STATUS_OF_DOWN)
                if self.last_down_obj is not None and self.continouns_status == FKCons.CONTINUOUS_STATUS_OF_DOWN:
                    # self.down_interval_list.append(self.last_down_obj)
                    self.down_interval_list = Logic.append(self.down_interval_list, self.last_down_obj)
                self.down_obj = Logic.get_base_obj(tick.current, tick.current)
                self.onchange_effective_status(FKCons.EFFECTIVE_STATUS_OF_UP)
                

    """
    出现反向突破时，进入新的有效方向状态，将之前的有效连续对象去掉，区间只保留起点
    """ 
    def onchange_effective_status(self, effective_status):
        # 向下的有效被打破
        self.effective_status = effective_status
    
    """
    初始化连续状态
    """
    def init_continuous_status(self, continuous_status):
        if self.continouns_status == FKCons.CONTINUOUS_STATUS_OF_NONE:
            self.continouns_status = continuous_status

    """
    处理反转
    有效状态向下时，如果向上区间列表长度大于0，当向下对象的终点比最后一个向上对象的起点更低时，发生反转，更新连续状态为向下
    有效状态向上时，如果向下区间列表长度大于0，当向上对象的终点比最后一个向下对象的起点更低时，发生反转，更新连续状态为向上
    """    
    def handle_effective_reverse(self):
        if self.effective_status == FKCons.EFFECTIVE_STATUS_OF_DOWN:
            up_interval_list_length = len(self.up_interval_list)
            if up_interval_list_length > 0:
                last_obj = self.up_interval_list[-1]
                if self.down_obj.end < last_obj.start and not self.down_obj.check:
                    self.down_obj.check = True
                    self.onchange_continouns_status(FKCons.CONTINUOUS_STATUS_OF_DOWN)
                    # if up_interval_list_length == 1:
                    #     self.up_interval_list = []
                    # else:
                    #     self.up_interval_list = []
                    #     self.up_interval_list.append(first_obj)
        elif self.effective_status == FKCons.EFFECTIVE_STATUS_OF_UP:
            down_interval_list_length = len(self.down_interval_list)
            if down_interval_list_length > 0:
                last_obj = self.down_interval_list[-1]
                if self.up_obj.end > last_obj.start and not self.up_obj.check:
                    self.up_obj.check = True
                    self.onchange_continouns_status(FKCons.CONTINUOUS_STATUS_OF_UP)
                    # if down_interval_list_length == 1:
                    #     self.down_interval_list = []
                    # else:
                    #     self.down_interval_list = []
                    #     self.down_interval_list.append(first_obj)

    def onchange_continouns_status(self, continouns_status):
        # 向下的有效被打破
        self.continouns_status = continouns_status
        if self.continouns_status == FKCons.CONTINUOUS_STATUS_OF_UP:
            self.down_continuous_obj = None
        elif self.continouns_status == FKCons.CONTINUOUS_STATUS_OF_DOWN:
            self.up_continuous_obj = None
   

    """
    处理有效区间连续
    连续状态向上时，如果向上区间列表不为空，更新向上连续对象
    连续状态向下时，如果向下区间列表不为空，更新向下连续对象
    """     
    def handle_effective_move(self):
        # 正向价格连续
        if self.continouns_status == FKCons.CONTINUOUS_STATUS_OF_UP:
            if len(self.up_interval_list) >= 2:
                first_obj = self.up_interval_list[0]
                last_obj = self.up_interval_list[-1]
                self.up_continuous_obj = Logic.build_continouns_obj(self.up_continuous_obj, first_obj.start, last_obj.end)
            elif len(self.up_interval_list) == 1:
                first_obj = self.up_interval_list[0]
                self.up_continuous_obj = Logic.build_continouns_obj(self.up_continuous_obj, first_obj.start, first_obj.end)
                self.init_effective_move_status(FKCons.MOVE_EFFECTIVE_STATUS_OF_UP)
            else:
                self.up_continuous_obj = None
        elif self.continouns_status == FKCons.CONTINUOUS_STATUS_OF_DOWN:
            if len(self.down_interval_list) >= 2:
                first_obj = self.down_interval_list[0]
                last_obj = self.down_interval_list[-1]
                self.down_continuous_obj = Logic.build_continouns_obj(self.down_continuous_obj, first_obj.start, last_obj.end)
            elif len(self.down_interval_list) == 1:
                first_obj = self.down_interval_list[0]
                self.down_continuous_obj = Logic.build_continouns_obj(self.down_continuous_obj, first_obj.start, first_obj.end)
                self.init_effective_move_status(FKCons.MOVE_EFFECTIVE_STATUS_OF_DOWN)
                # print(f"进入有效运动 down")
            else:
                self.down_continuous_obj = None

    """
    记录第一次进入有效运动的状态
    """ 
    def init_effective_move_status(self, move_status):
        if self.effective_move_status == FKCons.MOVE_EFFECTIVE_STATUS_OF_NONE:
            self.effective_move_status = move_status
        
    """
    如果向下连续对象不为None且向下连续对象的长度超过有效趋势长度，设置为有效趋势对象
    """
    def handle_effective_trend(self, tick):
        # if self.up_continuous_obj is not None and self.up_continuous_obj.length > self.effective_trend_length:
        #     self.effective_trend_obj = deepcopy(self.up_continuous_obj) 
        # else:
        #     self.effective_trend_obj = None

        if self.down_continuous_obj is not None and self.down_continuous_obj.length < self.effective_trend_length and self.down_continuous_obj.length > 10:
            self.effective_trend_obj = deepcopy(self.down_continuous_obj) 
        else:
            self.effective_trend_obj = None

    """
    如果向下区间列表不为空，当向上对象的终点比列表中第一个向下对象的起点高，就重置向下区间列表跟向下连续对象
    """
    def hanle_reverse_effective_move(self):
        # if len(self.up_interval_list) > 0:
        #     first_cd = self.up_interval_list[0]
        #     if self.down_obj.end < first_cd.start:
        #         self.onchange_effective_move_status(FKCons.EFFECTIVE_STATUS_OF_NONE)
        #         # print(f"出现了反向运动up to down {self.up_interval_list}")
        #         self.up_interval_list = []
        #         self.up_continuous_obj = None
        #         self.reset_extremum_end()
        #         print(f"跑到了这里来了 11111")
        if len(self.down_interval_list) > 0:
            first_cd = self.down_interval_list[0]
            if self.up_obj.end > first_cd.start:
                self.onchange_effective_move_status(FKCons.EFFECTIVE_STATUS_OF_NONE)
                self.down_interval_list = []
                self.down_continuous_obj = None
                self.reset_extremum_end()
                # print(f"出现了反向运动down to up")
    
    """
    反向运动之后触发事件
    """
    def onchange_effective_move_status(self, move_status):
            self.effective_move_status = move_status

        # if len(self.up_interval_list) > 0:
        #     first_cd = self.up_interval_list[0]
        #     if tick.current < first_cd.start:
        #         self.up_interval_list = []
        
        # if len(self.down_interval_list) > 0:
        #     down_first_cd = self.down_interval_list[0]
        #     if tick.current > down_first_cd.start:
        #         self.down_interval_list = []

    # todo 暂时没用上
    def reset_extremum_end(self):
        self.extremum_end = None

    """
    在平仓之后，如果终点下移就重置，否则不重置
    """
    def reset_up_factor_by_close(self):
        self.up_continuous_obj = None # 向上连续对象
        self.up_interval_list = [] # 向上y有效价格区间的list
        self.effective_trend_obj = None # 有效趋势
    
    """
    在平仓之后，如果盈利就重置，否则不重置
    """
    def reset_down_factor_by_close(self):
        self.down_continuous_obj = None # 向下连续对象
        self.down_interval_list = [] # 向下有效价格区间的list
        self.effective_trend_obj = None # 有效趋势

    