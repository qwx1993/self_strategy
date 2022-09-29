"""
history_unittest.py
history.py的单元测试，该单元测试用到了一系列测试用的csv文件，在test_csv文件中，包括：
* not_enough_data.csv：数据不足的csv
* speeding_falls_length_3.csv: 包含了10个参考波动的时间单位和一个周期的加速下跌（3次宽幅下跌），加速下跌的时间单位长度为3
* 1_speeding_fall.csv：包含了10个参考波动的时间单位和1个宽幅下跌
* open_fall.csv：包含了开盘下跌的情况，即当天第1分钟是下跌的，并且该分钟的开盘价小于（前一天的最后收盘价 - 前一天收盘前10分钟的平均波动的3倍）
"""

from datetime import datetime
from types import SimpleNamespace
from collections import deque
from constants import Constants
import unittest
import os
from history import History
from logic import Logic
from tick import Tick
from types import SimpleNamespace
import sys
from self_strategy.four_strategy import FourStrategy

from tick_logic import TickLogic

class TestTicks(unittest.TestCase):

	def get_data_from_test_csv(self, csv_file):
		ls1 = deque([])
		test_csv = open("test_csv/" + csv_file, "r")
		count = 0
		while True:
			line = test_csv.readline()
			if not line:
				break
			temp_array = line.split(',')
			if len(temp_array) > 0:
				# try:
				cd = TickLogic.tick_price_to_data_object(temp_array, count, line)
				cd.datetime = datetime.strptime(cd.datetime, '%Y-%m-%d %H:%M:%S.%f')
				cd.last_price = cd.current
				# except:
				# 	continue
				if len(ls1) >= Constants.REFERENCE_AND_SPEEDING_LENGTH:
					ls1.popleft()
				
				ls1.append(cd)

		test_csv.close()

		return ls1

	"""
	测试tick程序
	"""
	def test_tick(self):
		ls = self.get_data_from_test_csv('SA2301_tick.csv')
		fourStrategy = FourStrategy()
		last_cd = SimpleNamespace()
		last_cd.open = 100
		last_cd.high = 123
		last_cd.low = 90
		last_cd.close = 113
		last_cd.direction = Constants.DIRECTION_UP

		fourStrategy.close_price = 85
		fourStrategy.history.last_cd = last_cd
		fourStrategy.trade_action = Constants.ACTION_CLOSE_LONG # 开多

		for cd in ls:
			print(cd)
			fourStrategy.on_tick(cd)
			print(f"close_price => {fourStrategy.close_price}")

if __name__ == '__main__':
	unittest.main()