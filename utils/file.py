import os
import time
import logging

"""
初始化建立文件系统
"""
# def init_log(vt_symbol):
#     login_user = os.getlogin()
#     path = 'C:/Users/' + login_user + '/strategies/logs/'
#     if not os.path.exists(path):
#         os.mkdir(path)
#     day = time.strftime("%Y-%m-%d", time.localtime())
#     logging.basicConfig(level=logging.INFO, filename= path+ f"{vt_symbol}_{day}.log")

"""
获取日志对象
"""    
def get_logger(vt_symbol):
    logger = logging.getLogger(vt_symbol)
    # 创建一个handler，用于写入日志文件
    login_user = os.getlogin()
    path = 'C:/Users/' + login_user + '/strategies/logs/'
    if not os.path.exists(path):
        os.mkdir(path)
    day = time.strftime("%Y-%m-%d", time.localtime())
    filename = path+ f"{vt_symbol}_{day}.log"
    # 定义日志输出层级
    logger.setLevel(logging.DEBUG)
    # 如果handlers为空给logger对象绑定文件操作符
    if not logger.handlers:
        fh = logging.FileHandler(filename, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger