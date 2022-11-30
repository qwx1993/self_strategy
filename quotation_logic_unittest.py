from types import SimpleNamespace
from collections import deque
from constants import Constants
import unittest
import os
from logic import Logic
from quotation_logic import QuotationLogic
from types import SimpleNamespace

class TestQuotationLogics(unittest.TestCase):


	def get_data_from_test_csv(self, csv_file):
		ls1 = deque([])
		test_csv = open("test_csv/" + csv_file, "r")
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

	"""
	测试获取cr information
	"""
	def test_get_cr_information(self):
		l = []
		cr_obj = None 
		ls = self.get_data_from_test_csv('sc2211.INE_1m.csv')
		for cd in ls:
			l, cr_obj = QuotationLogic.get_cr_information(cd, l, cr_obj)
			print(f"list => {l} \ncr_obj => {cr_obj} \ncd => {cd} \n")
			print("--------------------------------------------------")

if __name__ == '__main__':
	unittest.main()