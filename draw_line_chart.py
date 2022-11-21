import numpy as np
import matplotlib.pyplot as mp
import sys
import platform
from datetime import datetime

class Draw_Linae_chart:
    current_page = 0
    BATCH_SIZE = 500

    filename = ""

    def __init__(self, filename):
        self.filename = filename
        sys.setrecursionlimit(3000)

    def key_press_event(self, event):
        if event.key == ']':
            self.current_page += 1
            try:
                self.draw_line_chart()
            except Exception as e:
                print(f"出错了，错误类型：{e}")
                self.current_page -= 1
                self.draw_line_chart()
        elif event.key == '[':
            if self.current_page > 0:
                self.current_page -= 1
                self.draw_line_chart()

    """
	根据filename指定的csv文件画出折线图
	"""
    def draw_line_chart(self):
        mp.close()
        self.fig, self.ax = mp.subplots()
        self.ax.clear()

        self.fig.canvas.mpl_connect('key_press_event', self.key_press_event)

        dates, prices,  = np.loadtxt(
            self.filename,
            skiprows=self.current_page * self.BATCH_SIZE,
            max_rows=self.BATCH_SIZE,
            delimiter=',',
            usecols=(0, 1,),
            unpack=True,
            dtype='M8[m], f8,',
        )
        # todo 此处看有么有比较直接转化的方法，
        format_dates = []
        for d in dates:
            format_dates.append(d.astype(datetime).strftime("%Y-%m-%d"))
        x = range(1, len(dates) + 1, 1)
        mp.plot(x, prices, marker='*')
        mp.xticks(x, format_dates, rotation=60)
        mp.title(self.filename.replace("temp-", ""))

        manager = mp.get_current_fig_manager()
        manager.resize(6000, 1800)
        mp.xlabel("日期")
        mp.ylabel("赚取总金额")
        if platform.system().lower() == "windows":
            mp.rcParams["font.sans-serif"] = ["SimHei"]
            mp.rcParams["font.family"] = "sans-serif"
        else:
            mp.rcParams["font.sans-serif"] = ["Arial Unicode MS"]
        mp.show()
