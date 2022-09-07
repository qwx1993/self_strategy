

class TickLogic:
    
    """
    判断是否保持方向不变
    """
    def keep_direction(cd, ls):
        first = ls[0]
        last = ls[-1]
        if first.current <= last.current <= cd.current:
            return True
        elif first.current >= last.current >= cd.current:
            return True
        else:
            return False 