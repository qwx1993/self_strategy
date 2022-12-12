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
        
        return obj