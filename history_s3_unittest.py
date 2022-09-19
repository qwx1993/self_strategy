from types import SimpleNamespace
from collections import deque
from constants import Constants
import unittest
import os
from history_s3 import HistoryS3
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
				cd = Logic.history_price_to_data_object(temp_array, line)
				# except:
				# 	continue
				if len(ls1) >= Constants.REFERENCE_AND_SPEEDING_LENGTH:
					ls1.popleft()
				
				ls1.append(cd)

		test_csv.close()

		return ls1

	def test_history_statistic_max_l_to_d(self):
		ls = self.get_data_from_test_csv('sc2211.INE_1m.csv')
		history = HistoryS3()
		for cd in ls:
			history.realtime_analysis1(cd)
		
		print(f"max_amplitude => {history.max_amplitude}")
		print(f"方向 => {history.breakthrough_direction}")
		print(f"R => {history.max_l_to_d_interval}")
		print(f"max_r => {history.max_r}")
		print(f"d_price => {history.extremum_d_price}")
		print(f"l_price => {history.extremum_l_price}")
		print(f"h_price => {history.h_price}")
		print(f"h_max_price => {history.h_price_max}")

	# def test_set_ml_price(self):
	# 	history = HistoryS3()
	# 	history.direction = Constants.DIRECTION_UP
	# 	cd = SimpleNamespace()
	# 	cd.open = 500
	# 	cd.high = 500
	# 	cd.low = 410
	# 	cd.close = 440
	# 	cd.direction = Constants.DIRECTION_DOWN
	# 	cd.datetime = '2022-09-13 21:18:00'

	# 	last_cd = SimpleNamespace()
	# 	last_cd.open = 450
	# 	last_cd.low = 440
	# 	last_cd.high =510
	# 	last_cd.close = 500
	# 	last_cd.direction = Constants.DIRECTION_UP
	# 	last_cd.datetime = '2022-09-13 21:17:00'
	# 	history.extremum_l_price = 55370
	# 	history.last_cd = last_cd
	# 	history.set_ml_price(cd)

	# """
	# 测试analysis
	# """
	# def test_analysis(self):
	# 	vt_symbol = 'sc2210.INE'
	# 	history = History()
	# 	history.analysis(vt_symbol, 1)
	# 	print(f"max_amplitude => {history.max_amplitude}")
	# 	print(f"方向 => {history.breakthrough_direction}")
	# 	print(f"R => {history.max_l_to_d_interval}")
	# 	print(f"max_r => {history.max_r}")
	# 	print(f"d_price => {history.extremum_d_price}")
	# 	print(f"l_price => {history.extremum_l_price}")
	# 	print(f"h_price => {history.h_price}")
	# 	print(f"h_max_price => {history.h_price_max}")
	# 	print(f"history_status => {history.history_status}")

if __name__ == '__main__':
	unittest.main()