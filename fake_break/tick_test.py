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
    open_price_effective_trend = None # 开仓时有效趋势的终点
    open_price_tick = None # 开仓时的tick数据
    need_check_close_effective_trend = None

 

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
        if self.trade_action is None and self.quotation.effective_trend_obj is not None and self.need_check_close_effective_trend is None:
            trend_obj = self.quotation.effective_trend_obj
            if trend_obj.direction == Cons.DIRECTION_UP:
                interval_list = self.quotation.up_interval_list
            else:
                interval_list = self.quotation.down_interval_list
            # if Trade.open_a_price(trend_obj, last_obj, self.quotation.effective_status, tick_obj):
            if Trade.open_a_price_by_list(trend_obj, interval_list, self.quotation.effective_status):
                if trend_obj.direction == Cons.DIRECTION_UP:
                    self.add_action(tick, Cons.ACTION_OPEN_SHORT, tick.current - self.unit_value)
                    self.open_price = tick.current - self.unit_value
                    self.open_price_tick = tick
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \ntrade_type => short \ntrend_obj => {trend_obj} \ntick => {tick} \ninterval_list => {interval_list} \ncontinouns_status => {self.quotation.continouns_status} \neffective_status => {self.quotation.effective_status} \ndown_obj => {self.quotation.down_obj}")
                    self.trade_action = Cons.ACTION_CLOSE_SHORT
                    self.open_price_effective_trend = deepcopy(self.quotation.effective_trend_obj)
                elif trend_obj.direction == Cons.DIRECTION_DOWN:
                    self.add_action(tick, Cons.ACTION_OPEN_LONG, tick.current + self.unit_value)
                    self.open_price = tick.current + self.unit_value
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \ntrade_type => long \ntrend_obj => {trend_obj} \ntick => {tick} \ninterval_list => {interval_list} \ncontinouns_status => {self.quotation.continouns_status} \neffective_status => {self.quotation.effective_status} \ndown_obj => {self.quotation.down_obj}")
                    self.trade_action = Cons.ACTION_CLOSE_LONG
                    self.open_price_effective_trend = deepcopy(self.quotation.effective_trend_obj)
        else:
            self.quotation.analysis(tick_obj)
            effective_status = self.quotation.effective_status
            if self.trade_action == Cons.ACTION_CLOSE_LONG:
                if Trade.close_a_price_by_list(self.trade_action, effective_status, self.quotation.last_up_interval_list):
                    self.add_action(tick, Cons.ACTION_CLOSE_LONG, tick.current - self.unit_value)
                    last_obj = self.quotation.up_interval_list[-1]
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction:long \ntick => {tick_obj} \neffective_status => {effective_status} \nlast_up_interval_list => {self.quotation.last_up_interval_list} \ndown_obj => {self.quotation.down_obj} \nopen_price_effective_trend => {self.open_price_effective_trend}")
                    self.after_close(tick_obj)
            elif self.trade_action == Cons.ACTION_CLOSE_SHORT:
                if Trade.close_a_price_by_list(self.trade_action, effective_status, self.quotation.last_down_interval_list):
                    self.add_action(tick, Cons.ACTION_CLOSE_SHORT, tick.current + self.unit_value)
                    last_obj = self.quotation.down_interval_list[-1]
                    self.log_obj.info(f"vt_symbol => {self.vt_symbol} \nclose_direction:short \ntick => {tick_obj} \neffective_status => {effective_status} \nlast_down_interval_list => {self.quotation.last_down_interval_list} \nup_obj => {self.quotation.up_obj} \nopen_price_effective_trend => {self.open_price_effective_trend}")
                    self.after_close(tick_obj)
        
        """
        当需要检查出场终点跟起点关系时
        """
        if self.need_check_close_effective_trend is not None:
            self.reset_up_factor_by_position()


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
        self.need_check_close_effective_trend = deepcopy(self.open_price_effective_trend)
        # self.reset_up_factor_by_position(tick)
    
    """
    如果开仓时有效趋势向上，当出场价格小于有效趋势的终点时，重置向上的因子，进入新循环
    如果开仓时有效趋势向下，当出场价格大于有效趋势的终点时，重置向下的因子，进入新循环
    """
    def reset_up_factor_by_position(self):
        if self.need_check_close_effective_trend.direction == Cons.DIRECTION_UP and self.quotation.effective_status == FBCons.EFFECTIVE_STATUS_OF_DOWN:
            last_up_obj = self.quotation.last_up_interval_list[-1]
            if last_up_obj.end < self.need_check_close_effective_trend.end:
                self.quotation.reset_up_factor_by_close()
                self.log_obj.info(f"reset_open_type => short \nlast_up_obj => {last_up_obj} \nneed_check_close_effective_trend => {self.need_check_close_effective_trend}")
            else:
                self.log_obj.info(f"not_reset_open_type => short \nlast_up_obj => {last_up_obj} \nneed_check_close_effective_trend => {self.need_check_close_effective_trend}")
            self.need_check_close_effective_trend = None
        elif self.need_check_close_effective_trend.direction == Cons.DIRECTION_DOWN and self.quotation.effective_status == FBCons.EFFECTIVE_STATUS_OF_UP:
            last_down_obj = self.quotation.last_down_interval_list[-1]
            if last_down_obj.end > self.need_check_close_effective_trend.end:
                pass
    

    def reset_up_factor_by_win(self, tick):
        if self.open_price_effective_trend.direction == Cons.DIRECTION_UP:
            if (self.open_price_tick.current - tick.current) > 2*self.unit_value:
                self.quotation.reset_up_factor_by_close()
                # result = self.open_price_tick.current - tick.current 
                # print(f"open_price_tick => {self.open_price_tick.current} tick.current => {tick.current} result => {result}")
            elif (tick.current - self.open_price_tick.current) >2*self.unit_value:
                pass