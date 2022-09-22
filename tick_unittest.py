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
	# def test_tick(self):
	# 	ls = self.get_data_from_test_csv('SA2301_tick.csv')
	# 	tick = Tick()
	# 	for cd in ls:
	# 		if tick.current_status == Constants.STATUS_NONE:  # 寻找振荡
	# 			tick.status_none(cd)
	# 		elif tick.current_status == Constants.STATUS_FIND_D1:  # 寻找D1
	# 			tick.find_d(cd)
	# 		elif tick.current_status == Constants.NON_ACCELERATING_OSCILLATION:  # 非加速振荡
	# 			tick.non_accelerating_oscillation(cd)
	# 		elif tick.current_status == Constants.TICK_STATUS_PAUSE:
	# 			print(f"跑完 => 开盘价为 {tick.open_price} datetime => {cd.datetime}")
	# 	print(f"方向 => {tick.breakthrough_direction}")
	# 	print(f"R => {tick.max_l_to_d_interval}")
	# 	print(f"max_r => {tick.max_r}")
	# 	print(f"d_price => {tick.extremum_d.current}")
	# 	print(f"l_price => {tick.extremum_l.current}")
	# 	print(f"h_price => {tick.h_price}")

		# print(f"h_max_price => {history.h_price_max}")

		# print(f"方向 => {history.breakthrough_direction}")
		# print(f"R => {history.max_l_to_d_interval}")
		# print(f"max_r => {history.max_r}")
		# print(f"d_price => {history.extremum_d_price}")
		# print(f"l_price => {history.extremum_l_price}")
		# print(f"h_price => {history.h_price}")
		# print(f"h_max_price => {history.h_price_max}")

	"""
	测试合成tick数据
	"""
	def test_merge_ticks_to_m1(self):
		s_l = []
		ls = self.get_data_from_test_csv('test_combine.csv')
		for tick_obj in ls:
			s_l.append(tick_obj)
			merge = TickLogic.merge_ticks_to_m1(s_l)
			print(f"合成的结果 => {merge}")

if __name__ == '__main__':
	unittest.main()