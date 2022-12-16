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
from self_strategy.fake_break.trade import Trade
from self_strategy.constants import Constants as Cons
from self_strategy.fake_break.constants import Constants as FBCons


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

        if self.trade_action is None and self.quotation.effective_trend_obj is not None:
            trend_obj = self.quotation.effective_trend_obj
            if trend_obj.direction == Cons.DIRECTION_UP:
                last_obj = self.quotation.last_up_obj
            else:
                last_obj = self.quotation.last_down_obj
            if Trade.open_a_price(trend_obj, last_obj, tick_obj):
                if trend_obj.direction == Cons.DIRECTION_UP:
                    self.add_action(tick, Cons.ACTION_OPEN_SHORT, tick.current - self.unit_value)
                    self.open_price = tick.current - self.unit_value
                    self.open_price_tick = tick
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \ntrade_type => short \ntrend_obj => {trend_obj} \ntick => {tick} \nlast_obj => {last_obj}")
                    self.trade_action = Cons.ACTION_CLOSE_SHORT
                elif trend_obj.direction == Cons.DIRECTION_DOWN:
                    self.add_action(tick, Cons.ACTION_OPEN_LONG, tick.current + self.unit_value)
                    self.open_price = tick.current + self.unit_value
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \ntrade_type => long \ntrend_obj => {trend_obj} \ntick => {tick} \nlast_obj => {last_obj}")
                    self.trade_action = Cons.ACTION_CLOSE_LONG
            self.quotation.analysis(tick_obj) 
        else:
            self.quotation.analysis(tick_obj)
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if Trade.close_a_price(self.trade_action, self.quotation.continouns_status):
                    self.add_action(tick, Cons.ACTION_CLOSE_LONG, tick.current - self.unit_value)
                    last_obj = self.quotation.up_interval_list[-1]
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction:long \ntick => {tick_obj} \nlast_up_obj => {last_obj} \ndown_obj => {self.quotation.down_obj} \ncontinouns_status => {self.quotation.continouns_status}")
                    self.after_close(tick_obj)
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                if Trade.close_a_price(self.trade_action, self.quotation.continouns_status):
                    self.add_action(tick, Cons.ACTION_CLOSE_SHORT, tick.current + self.unit_value)
                    last_obj = self.quotation.down_interval_list[-1]
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction:short \ntick => {tick_obj} \nlast_down_obj => {last_obj} \nup_obj => {self.quotation.up_obj} \ncontinouns_status => {self.quotation.continouns_status}")
                    self.after_close(tick_obj)


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
    
    """
    写入交易动作
    """ 
    def add_action(self, cd, action, price):
        record = {
            "price": price,
            "action": action,
            "datetime": cd.datetime
        }

        self.actions.append(record)
    
    """
    平仓之后的动作
    """
    def after_close(self, tick):
        self.trade_action = None