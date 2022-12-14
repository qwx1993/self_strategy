from types import SimpleNamespace

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
        
        return obj
    
    """
    刷新统计的基础对象
    """
    def refresh_base_obj(obj, end):
        obj.end = end
        obj.length = abs(end - obj.start)
        
        return obj