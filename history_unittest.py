"""
history_unittest.py
history.py的单元测试，该单元测试用到了一系列测试用的csv文件，在test_csv文件中，包括：
* not_enough_data.csv：数据不足的csv
* speeding_falls_length_3.csv: 包含了10个参考波动的时间单位和一个周期的加速下跌（3次宽幅下跌），加速下跌的时间单位长度为3
* 1_speeding_fall.csv：包含了10个参考波动的时间单位和1个宽幅下跌
* open_fall.csv：包含了开盘下跌的情况，即当天第1分钟是下跌的，并且该分钟的开盘价小于（前一天的最后收盘价 - 前一天收盘前10分钟的平均波动的3倍）
"""

from types import SimpleNamespace
from collections import deque
from constants import Constants
import unittest
import os
from history import History
from logic import Logic
from types import SimpleNamespace
import sys

class TestHistorys(unittest.TestCase):

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
				cd = Logic.history_price_to_data_object(temp_array, count, line)
				# except:
				# 	continue
				if len(ls1) >= Constants.REFERENCE_AND_SPEEDING_LENGTH:
					ls1.popleft()
				
				ls1.append(cd)

		test_csv.close()

		return ls1

	# def test_history_statistic_max_l_to_d(self):
	# 	ls = self.get_data_from_test_csv('000001.XSHE_1m.csv')
	# 	history = History()
	# 	for cd in ls:
	# 		if history.history_status == Constants.HISTORY_STATUS_OF_NONE: 
	# 			history.histoty_status_none(cd)
	# 		elif history.history_status == Constants.HISTORY_STATUS_OF_TREND:  # 趋势分析中
	# 			history.statistic(cd)
	# 		history.last_cd = cd
		
	# 	print(f"max_amplitude => {history.max_amplitude}")
	# 	print(f"方向 => {history.breakthrough_direction}")
	# 	print(f"R => {history.max_l_to_d_interval}")
	# 	print(f"max_r => {history.max_r}")
	# 	print(f"d_price => {history.extremum_d_price}")
	# 	print(f"l_price => {history.extremum_l_price}")
	# 	print(f"h_price => {history.h_price}")
	# 	print(f"h_max_price => {history.h_price_max}")
	
	"""
	测试analysis
	"""
	def test_analysis(self):
		vt_symbol = 'SA301.CZCE'
		history = History()
		history.analysis(vt_symbol, 1)
		print(f"max_amplitude => {history.max_amplitude}")
		print(f"方向 => {history.breakthrough_direction}")
		print(f"R => {history.max_l_to_d_interval}")
		print(f"max_r => {history.max_r}")
		print(f"d_price => {history.extremum_d_price}")
		print(f"l_price => {history.extremum_l_price}")
		print(f"h_price => {history.h_price}")
		print(f"h_max_price => {history.h_price_max}")

if __name__ == '__main__':
	unittest.main()