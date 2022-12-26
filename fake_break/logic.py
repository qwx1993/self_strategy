from types import SimpleNamespace
from self_strategy.constants import Constants

class Logic:
    """
    设置统计的基础对象
    """
    def get_base_obj(start, end):
        obj = SimpleNamespace()
        obj.start = start
        obj.end = end
        obj.length = abs(start - end)
        obj.check = False
        if obj.end > obj.start:
            obj.direction = Constants.DIRECTION_UP
        elif obj.end < obj.start:
            obj.direction = Constants.DIRECTION_DOWN
        else:
            obj.direction = Constants.DIRECTION_NONE
        
        return obj
    
    """
    刷新统计的基础对象
    """
    def refresh_base_obj(obj, end):
        obj.end = end
        obj.length = abs(end - obj.start)
        if obj.end > obj.start:
            obj.direction = Constants.DIRECTION_UP
        elif obj.end < obj.start:
            obj.direction = Constants.DIRECTION_DOWN
        else:
            obj.direction = Constants.DIRECTION_NONE
        return obj

    """
    构建连续对象
    """
    def build_continouns_obj(continouns_obj, start, end):
        if continouns_obj is None:
            continouns_obj = SimpleNamespace()
        continouns_obj.start = start
        continouns_obj.end = end
        if continouns_obj.end > continouns_obj.start:
            continouns_obj.direction = Constants.DIRECTION_UP
        elif continouns_obj.end < continouns_obj.start:
            continouns_obj.direction = Constants.DIRECTION_DOWN
        else:
            continouns_obj.direction = Constants.DIRECTION_NONE
        
        continouns_obj.length = abs(continouns_obj.start - continouns_obj.end)
        
        return continouns_obj

    """
    只保留第一个跟最后一个
    """
    def append(l, obj):
        l_len = len(l)
        if l_len == 0:
            l.append(obj)
        else:
            first_obj = l[0]
            l = []
            l = [first_obj, obj]
        return l
    
    """
    只保留最后两个
    """
    def append_last(l, obj):
        l_len = len(l)
        if l_len < 2:
            l.append(obj)
        else:
            last_obj = l[-1]
            l = []
            l = [last_obj, obj]
        
        return l
    
    """
    是否为终点的极值，现在只延续终点的极值进行开仓
    """
    def is_extremum_end(direction, extremum_end, end_value):
        # return True
        if extremum_end is None:
            return True
        
        if direction == Constants.DIRECTION_UP:
            if end_value > extremum_end:
                return True
        elif direction == Constants.DIRECTION_DOWN:
            if end_value < extremum_end:
                return True
            
        return False