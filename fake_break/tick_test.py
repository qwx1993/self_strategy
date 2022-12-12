from types import SimpleNamespace
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

from self_strategy.fake_break.quotation import Quotation
from self_strategy.utils import (
    file,
)
from copy import deepcopy

# tick 数据测试
class TickTest():
    vt_symbol = None # 合约名
    log_obj = None  # 日志对象
    history = None # 行情实例
    # 定义参数
    hand_number = 1
    trade_action = None 
    actions = [] # 交易动作
    unit_value = None

 

    # 添加参数和变量名到对应的列表
    def __init__(self, 
        vt_symbol,
        unit_value,
           ):
        """"""
        self.vt_symbol = vt_symbol
        self.unit_value = unit_value

        """
        初始化日志
        """
        self.log_obj = file.get_logger(self.vt_symbol)
        self.quotation = Quotation(self.unit_value)
        self.actions = []

    """
    通过该函数收到Tick推送。
    """     
    def on_tick(self, tick):
        tick_obj = self.get_tick_object(tick)
        self.quotation.analysis(tick_obj)


    """
    通过该函数收到新的1分钟K线推送。
    """
    def on_bar(self, cd):
        pass

    """
    获取tick对象
    """
    def get_tick_object(self, tick):
        cd = SimpleNamespace()
        cd.datetime = tick.datetime
        cd.current = tick.current
        return cd