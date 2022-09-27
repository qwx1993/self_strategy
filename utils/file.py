import os
import time
import logging
"""
初始化建立文件系统
"""
def init_log(vt_symbol):
    path = 'C:/Users/Administrator/strategies/logs/'
    if not os.path.exists(path):
        os.mkdir(path)
    day = time.strftime("%Y-%m-%d", time.localtime())
    logging.basicConfig(level=logging.INFO, filename= path+ f"{vt_symbol}_{day}.log")