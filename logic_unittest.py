"""
logic_unittest.py
logic.py的单元测试，该单元测试用到了一系列测试用的csv文件，在test_csv文件中，包括：
* not_enough_data.csv：数据不足的csv
* speeding_falls_length_3.csv: 包含了10个参考波动的时间单位和一个周期的加速下跌（3次宽幅下跌），加速下跌的时间单位长度为3
* 1_speeding_fall.csv：包含了10个参考波动的时间单位和1个宽幅下跌
* open_fall.csv：包含了开盘下跌的情况，即当天第1分钟是下跌的，并且该分钟的开盘价小于（前一天的最后收盘价 - 前一天收盘前10分钟的平均波动的3倍）
"""

from re import L
from types import SimpleNamespace
from collections import deque
from constants import Constants
import unittest
import os
from logic import Logic
from types import SimpleNamespace

class TestLogics(unittest.TestCase):
	
	# def test_revert_n_lines(self):
	# 	file = open('test_csv/simple_test.csv', 'r')
	# 	line1 = file.readline()
	# 	line2 = file.readline()
	# 	line3 = file.readline()

	# 	Logic.revert_n_lines(1, file)
	# 	line_x =  file.readline()
	# 	self.assertEqual(line_x, line3)

	# 	Logic.revert_n_lines(2, file)
	# 	line_x = file.readline()
	# 	self.assertEqual(line_x, line2)

	# 	file.readline()
	# 	file.readline()

	# 	Logic.revert_n_lines(4, file)
	# 	line_x = file.readline()
	# 	self.assertEqual(line_x, line1)
	# 	file.close()

	# def test_truncate_last_n_lines(self):
	# 	filename = 'test_csv/temp_test.csv'
	# 	file = open(filename, 'w+')
	# 	file.write('------ temp line 1\n')
	# 	file.write('------ temp line 2\n')
	# 	file.write('------ temp line 3\n')

	# 	Logic.truncate_last_n_lines(2, file)

	# 	file.seek(file.tell(), os.SEEK_SET)

	# 	file.write('hello world\n')
	# 	file.close()
	# 	os.remove(filename)

	"""
	检测是否需要合并
	"""
	def test_need_merge(self):
# NI2301,2022-09-16 21:36:00,184310.0,184310.0,183800.0,183990.0
# NI2301,2022-09-16 21:37:00,183990.0,184080.0,183990.0,184080.0
# NI2301,2022-09-16 21:38:00,184080.0,184200.0,183860.0,183860.0
		last_cd = SimpleNamespace()
		# 方向向上
		last_cd.open = 184310.0
		last_cd.low = 183800.0
		last_cd.high = 184310.0
		last_cd.close = 183990.0
		last_cd.direction = Constants.DIRECTION_DOWN

		cd = SimpleNamespace()
		cd.open =  183990.0
		cd.low = 183990.0
		cd.high = 184080.0
		cd.close = 184080.0
		cd.direction = Constants.DIRECTION_UP

		self.assertTrue(Logic.need_merge(last_cd, cd))
		prices = []
		prices.append(last_cd)
		prices.append(cd)
		merge = Logic.merge_multiple_time_units(prices)

		print(merge)


	"""
	测试是否为最后一分钟
	"""
	def test_is_last_minute(self):
		date_str1 = '2014-08-23 12:33:00'
		self.assertFalse(Logic.is_last_minute(date_str1))

		date_str2 = '2015-04-15 15:15:00'
		self.assertTrue(Logic.is_last_minute(date_str2))

		date_str3 = '2019-04-15 15:00:00'
		self.assertTrue(Logic.is_last_minute(date_str3))

	"""
	从test.csv中获取一个记录了各个时间单位的deque的数组
	"""
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
				try:
					cd = Logic.raw_to_data_object(temp_array, count, line)
				except:
					continue
				if len(ls1) >= Constants.REFERENCE_AND_SPEEDING_LENGTH:
					ls1.popleft()
				
				ls1.append(cd)

		test_csv.close()
		return ls1
	
	# def test_is_firm_offer_start_minute(self):
	# 	datetime_str = "2022-08-29 21:00:00"
	# 	self.assertTrue(Logic.is_firm_offer_start_minute(datetime_str))

	
	# def test_is_high_point(self):
	# 	direction = Constants.DIRECTION_UP
	# 	last_cd = SimpleNamespace()
	# 	cd = SimpleNamespace()
	# 	# 情况一
	# 	cd.open = 100
	# 	cd.low = 98 
	# 	cd.high = 105
	# 	cd.close = 102
	# 	cd.direction = Constants.DIRECTION_UP
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))
	# 	# 情况二
	# 	# if cd.direction == Constants.DIRECTION_DOWN and cd.open == cd.high:
	# 	cd.direction = Constants.DIRECTION_DOWN
	# 	cd.open = 100
	# 	cd.low = 98
	# 	cd.high = 100
	# 	cd.close = 98

	# 	last_cd.open = 90
	# 	last_cd.low = 85 
	# 	last_cd.high = 100
	# 	last_cd.close = 100
	# 	last_cd.direction = Constants.DIRECTION_UP
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))

	# 	# 情况三
	# 	# last_cd.close < cd.open:
	# 	last_cd.close = 98
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))

	# 	# 情况四
	# 	# last_cd.direction == Constants.DIRECTION_UP and last_cd.high == last_cd.close and last_cd.close <= cd.open
	# 	last_cd.direction = Constants.DIRECTION_UP
	# 	last_cd.open = 90
	# 	last_cd.low = 85
	# 	last_cd.close = 95
	# 	last_cd.high = 95
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))

	# 	# if last_cd.open == last_cd.close == last_cd.high > last_cd.low and last_cd.close <= cd.open:
	# 	last_cd.open = 95
	# 	last_cd.close = last_cd.close = last_cd.high = 95
	# 	last_cd.low = 90
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))
	# 	# 情况五
	# 	# cd.low < cd.close and cd.low < cd.open
	# 	direction = Constants.DIRECTION_DOWN
	# 	cd.open = 100
	# 	cd.high = 105
	# 	cd.low = 90
	# 	cd.close = 95
	# 	cd.direction = Constants.DIRECTION_DOWN
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))

	# 	# 情况六
	# 	# cd.direction == Constants.DIRECTION_UP and cd.open == cd.low:
	# 	cd.direction = Constants.DIRECTION_UP
	# 	cd.open = 100
	# 	cd.low = 100
	# 	cd.high = 105
	# 	cd.close = 102
	# 	# last_cd.close > cd.open
	# 	last_cd.close = 105
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))
	# 	# 情况七
	# 	# last_cd.direction == Constants.DIRECTION_DOWN and last_cd.low == last_cd.close and last_cd.close >= cd.open
	# 	last_cd.direction = Constants.DIRECTION_DOWN
	# 	last_cd.low = last_cd.close = 105
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))
	# 	# 情况八
	# 	# last_cd.direction == Constants.DIRECTION_UP and last_cd.high > last_cd.close and last_cd.close >= cd.open
	# 	last_cd.direction = Constants.DIRECTION_UP
	# 	last_cd.open = 90
	# 	last_cd.low = 85
	# 	last_cd.high = 105
	# 	last_cd.close = 100
	# 	self.assertTrue(Logic.is_high_point(direction, last_cd, cd))
	# 	# 情况九
	# 	# last_cd.open == last_cd.close == last_cd.low < last_cd.high and last_cd.close >= cd.open
	# 	last_cd.open = 101
	# 	last_cd.high = 105
	# 	last_cd.low = 101
	# 	last_cd.close = 101
	# 	self.assertTrue(Logic.is_high_point(direction,last_cd, cd))

	"""
	振荡区间
	"""
	# def test_flunc_check_oscillating_interval(self):
	# 	ls = self.get_data_from_test_csv("check_oscillating_interval_success.csv")
	# 	is_oscillating_interval, b1_to_b2_interval, b_list, current_oscillation_number = Logic.check_oscillating_interval(ls)
	# 	self.assertTrue(is_oscillating_interval)

	# 	cd = SimpleNamespace()
	# 	cd.high = 7519.8
	# 	cd.low = 7508.4
	# 	cd.close = 7510.1
	# 	ls = [cd]
	# 	is_oscillating_interval, b1_to_b2_interval, b_list, current_oscillation_number = Logic.check_oscillating_interval(ls)
	# 	self.assertTrue(is_oscillating_interval)

	"""
	测试是否突破
	"""
	# def test_has_break_through(self):
	# 	ls = self.get_data_from_test_csv("break_through_success.csv")
	# 	cd = ls.pop()
	# 	is_oscillating_interval, b1_to_b2_interval, b_list, current_oscillation_number = Logic.check_oscillating_interval(ls)
	# 	self.assertTrue(is_oscillating_interval)
	# 	self.assertTrue(Logic.has_break_through(cd, b1_to_b2_interval))

	# 	ls = self.get_data_from_test_csv("break_through_fail.csv")
	# 	cd = ls.pop()
	# 	is_oscillating_interval, b1_to_b2_interval, b_list, current_oscillation_number = Logic.check_oscillating_interval(ls)
	# 	self.assertTrue(is_oscillating_interval)
	# 	self.assertFalse(Logic.has_break_through(cd, b1_to_b2_interval))

	"""
	测试在振荡区间范围内
	"""
	# def test_is_out_range(self):
	# 	ls = self.get_data_from_test_csv("break_through_success.csv")
	# 	# 测试范围之内
	# 	reference_point_a_price = 7508.4
	# 	amplitude_ratio = 0.003
	# 	self.assertFalse(Logic.is_out_range(ls[0], reference_point_a_price, amplitude_ratio))
	# 	# 测试超出范围
	# 	reference_point_a_price = 7481
	# 	amplitude_ratio = 0.003
	# 	self.assertTrue(Logic.is_out_range(ls[0], reference_point_a_price, amplitude_ratio))

	"""
	情况一
	"""
	# def test_situation1(self):
	# 	reference_point_d = SimpleNamespace()
	# 	reference_point_d.high = 7519.8
	# 	reference_point_d.low = 7508.4

	# 	d2 = SimpleNamespace()
	# 	d2.high = 7520.8
	# 	d2.low = 7503.4
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
	# 	self.assertTrue(Logic.situation1(d2, breakthrough_direction, reference_point_d))
	# 	# 开空
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
	# 	self.assertTrue(Logic.situation1(d2, breakthrough_direction, reference_point_d))
	# 	# 不符合条件
	# 	d2.low = 7510.0
	# 	self.assertFalse(Logic.situation1(d2, breakthrough_direction, reference_point_d))

	"""
	情况二
	"""
	# def test_situation2(self):
	# 	reference_point_d = SimpleNamespace()
	# 	reference_point_d.high = 7519.8
	# 	reference_point_d.low = 7508.4

	# 	d2 = SimpleNamespace()
	# 	d2.high = 7520.8
	# 	d2.low = 7503.4
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
	# 	# 情况一
	# 	b1_price = 7450
	# 	self.assertFalse(Logic.situation2(d2, breakthrough_direction, reference_point_d, b1_price))
	# 	# 满足情况二
	# 	d2.high = 7518.3
	# 	self.assertTrue(Logic.situation2(d2, breakthrough_direction, reference_point_d, b1_price))
	# 	# low 比 b1_price小
	# 	d2.low = 7449
	# 	self.assertFalse(Logic.situation2(d2, breakthrough_direction, reference_point_d, b1_price))

	"""
	止盈
	"""
	# def test_stop_surplus(self):
	# 	cd = SimpleNamespace()
	# 	cd.high = 7519.8
	# 	cd.close = 7502.1
	# 	cd.low = 7493.2
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
	# 	dn_to_ln_max = 10
	# 	self.assertTrue(Logic.stop_surplus(cd, dn_to_ln_max))
	# 	# 没有超过最大的下降幅度
	# 	dn_to_ln_max = 30
	# 	self.assertFalse(Logic.stop_surplus(cd, dn_to_ln_max))
	# 	# 开空
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
	# 	self.assertFalse(Logic.stop_surplus(cd, dn_to_ln_max))
	# 	dn_to_ln_max = 7
	# 	self.assertTrue(Logic.stop_surplus(cd, dn_to_ln_max))

	"""
	逆趋势
	"""
	# def test_is_counter_trend(self):
	# 	cd = SimpleNamespace()
	# 	cd.high = 7519.8
	# 	cd.close = 7452.1
	# 	cd.low = 7423.2
	# 	cd.open = 7459.1
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
	# 	max_r = 40
	# 	self.assertTrue(Logic.is_counter_trend(cd, max_r, breakthrough_direction))
	# 	# 没有出现逆趋势
	# 	max_r = 70
	# 	self.assertFalse(Logic.is_counter_trend(cd, max_r, breakthrough_direction))
	# 	# 开空
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
	# 	# 没有出现逆趋势
	# 	self.assertFalse(Logic.is_counter_trend(cd, max_r, breakthrough_direction))
	# 	# 出现逆趋势
	# 	max_r = 20
	# 	self.assertTrue(Logic.is_counter_trend(cd, max_r, breakthrough_direction))

	"""
	情况1止损
	"""
	# def test_situation1_stop_loss(self):
	# 	cd = SimpleNamespace()
	# 	cd.high = 7559.8
	# 	cd.close = 7459.1
	# 	cd.low = 7423.2

	# 	stop_loss_ln_price = 7453.1
	# 	# 开多
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
	# 	self.assertTrue(Logic.situation1_stop_loss(cd, stop_loss_ln_price, breakthrough_direction))
	# 	cd.close = 7455.1
	# 	self.assertTrue(Logic.situation1_stop_loss(cd, stop_loss_ln_price, breakthrough_direction))
	# 	# 开空
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
	# 	cd.close = 7455.1
	# 	self.assertTrue(Logic.situation1_stop_loss(cd, stop_loss_ln_price, breakthrough_direction))
	# 	cd.high = 7451.1
	# 	self.assertFalse(Logic.situation1_stop_loss(cd, stop_loss_ln_price, breakthrough_direction))

	"""
	情况二开仓
	"""
	# def test_situation2_open_a_position(self):
	# 	cd = SimpleNamespace()
	# 	cd.high = 7519.8
	# 	cd.close = 7452.1
	# 	cd.low = 7423.2

	# 	appear_3t1_ln = True
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
	# 	ln_price = 7420.1
	# 	max_l_to_h = 50
	# 	self.assertTrue(Logic.situation2_open_a_position(cd, breakthrough_direction, ln_price, max_l_to_h))
	# 	#  没有超过ln
	# 	ln_price = 7425.1
	# 	self.assertFalse(Logic.situation2_open_a_position(cd, breakthrough_direction, ln_price, max_l_to_h))
	# 	# 开空的情况
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
	# 	ln_price = 7525.1
	# 	self.assertTrue(Logic.situation2_open_a_position(cd,  breakthrough_direction, ln_price, max_l_to_h))
	# 	ln_price = 7517.7
	# 	self.assertFalse(Logic.situation2_open_a_position(cd, breakthrough_direction, ln_price, max_l_to_h))

	"""
	情况二止损
	"""
	# def test_situation2_stop_loss(self):
	# 	cd = SimpleNamespace()
	# 	cd.high = 7519.8
	# 	cd.close = 7452.1
	# 	cd.low = 7423.2
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_UP
	# 	ln_price = 7428.2
	# 	self.assertTrue(Logic.situation2_stop_loss(cd, breakthrough_direction, ln_price))
	# 	ln_price = 7420
	# 	self.assertFalse(Logic.situation2_stop_loss(cd, breakthrough_direction, ln_price))
	# 	# 逆趋势
	# 	breakthrough_direction = Constants.BREAKTHROUGH_DIRECTION_DOWN
	# 	ln_price = 7516.8
	# 	self.assertTrue(Logic.situation2_stop_loss(cd, breakthrough_direction, ln_price))
	# 	ln_price = 7530.1
	# 	self.assertFalse(Logic.situation2_stop_loss(cd, breakthrough_direction, ln_price))

	# def test_calculate_rate(self):
	# 	actions1 = [
	# 		{
	# 			"action": Constants.ACTION_OPEN_SHORT,
	# 			"price": 5,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_CLOSE_SHORT,
	# 			"price": 3,
	# 		},
	# 	]
	# 	result1 = Logic.calculate_rate(actions1)
	# 	# num_trade = 0  # 开多次数
	# 	# reverse_num_trade = 0  # 逆趋势开多次数
	# 	# num_short = 0  # 开空次数
	# 	# reverse_num_short = 0  # 逆趋势开空次数
	# 	# num_win = 0  # 胜利次数
	# 	# num_lose = 0  # 失败次数
	# 	# win_amount = 0  # 赢钱/数钱的具体值
	# 	self.assertEqual(result1["num_trade"], 0)
	# 	self.assertEqual(result1["reverse_num_trade"], 0)
	# 	self.assertEqual(result1["num_short"], 1)
	# 	self.assertEqual(result1["reverse_num_short"], 0)
	# 	self.assertEqual(result1["num_win"], 1)
	# 	self.assertEqual(result1["num_lose"], 0)
	# 	self.assertEqual(result1["win_amount"], 2)
	# 	actions2 = [
	# 		{
	# 			"action": Constants.ACTION_OPEN_LONG,
	# 			"price": 5,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_CLOSE_LONG,
	# 			"price": 8,
	# 		},
	# 	]
	# 	result2 = Logic.calculate_rate(actions2)
	# 	self.assertEqual(result2["num_trade"], 1)
	# 	self.assertEqual(result2["reverse_num_trade"], 0)
	# 	self.assertEqual(result2["num_short"], 0)
	# 	self.assertEqual(result2['reverse_num_short'], 0)
	# 	self.assertEqual(result2["num_win"], 1)
	# 	self.assertEqual(result2["num_lose"], 0)
	# 	self.assertEqual(result2["win_amount"], 3)
	# 	#  逆趋势开空
	# 	actions3 = [
	# 		{
	# 			"action": Constants.ACTION_REVERSE_OPEN_SHORT,
	# 			"price": 5,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_CLOSE_SHORT,
	# 			"price": 8,
	# 		},
	# 	]
	# 	result3 = Logic.calculate_rate(actions3)
	# 	self.assertEqual(result3["num_trade"], 0)
	# 	self.assertEqual(result3["reverse_num_trade"], 0)
	# 	self.assertEqual(result3["num_short"], 0)
	# 	self.assertEqual(result3['reverse_num_short'], 1)
	# 	self.assertEqual(result3["num_win"], 0)
	# 	self.assertEqual(result3["num_lose"], 1)
	# 	self.assertEqual(result3["win_amount"], -6)

	# 	# 逆趋势开多
	# 	actions4 = [
	# 		{
	# 			"action": Constants.ACTION_REVERSE_OPEN_LONG,
	# 			"price": 10,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_CLOSE_LONG,
	# 			"price": 15
	# 		}
	# 	]
	# 	result4 = Logic.calculate_rate(actions4)
	# 	self.assertEqual(result4["num_trade"], 0)
	# 	self.assertEqual(result4["reverse_num_trade"], 1)
	# 	self.assertEqual(result4["num_short"], 0)
	# 	self.assertEqual(result4["reverse_num_short"], 0)
	# 	self.assertEqual(result4["num_win"], 1)
	# 	self.assertEqual(result4["num_lose"], 0)
	# 	self.assertEqual(result4["win_amount"], 10)

	# 	actions5 = [
	# 		{
	# 			"action": Constants.ACTION_OPEN_SHORT,
	# 			"price": 10,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_CLOSE_SHORT,
	# 			"price": 15
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_OPEN_LONG,
	# 			"price": 10
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_CLOSE_LONG,
	# 			"price": 17
	# 		}
	# 	]
	# 	result5 = Logic.calculate_rate(actions5)
	# 	self.assertEqual(result5["num_trade"], 0)
	# 	self.assertEqual(result5["reverse_num_trade"], 1)
	# 	self.assertEqual(result5["num_short"], 1)
	# 	self.assertEqual(result5["reverse_num_short"], 0)
	# 	self.assertEqual(result5["num_win"], 1)
	# 	self.assertEqual(result5["num_lose"], 1)
	# 	self.assertEqual(result5["win_amount"], 9)

	# 	actions6 = [
	# 		{
	# 			"action": Constants.ACTION_OPEN_SHORT,
	# 			"price": 100
	# 		},
	# 		{
	# 			"action": Constants.ACTION_CLOSE_SHORT,
	# 			"price": 105  # -5
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_OPEN_LONG,
	# 			"price": 107
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_CLOSE_LONG,
	# 			"price": 113  # + 12
	# 		}
	# 	]

	# 	result6 = Logic.calculate_rate(actions6)
	# 	self.assertEqual(result6["num_trade"], 0)
	# 	self.assertEqual(result6["reverse_num_trade"], 1)
	# 	self.assertEqual(result6["num_short"], 1)
	# 	self.assertEqual(result6["reverse_num_short"], 0)
	# 	self.assertEqual(result6["num_win"], 1)
	# 	self.assertEqual(result6["num_lose"], 1)
	# 	self.assertEqual(result6["win_amount"], 7)

	# 	# 新开多，在逆趋势开多，在逆趋势开空
	# 	actions7 = [
	# 		{
	# 			"action": Constants.ACTION_OPEN_LONG,
	# 			"price": 5,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_CLOSE_LONG,
	# 			"price": 1,  # -4
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_OPEN_LONG,
	# 			"price": 8,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_CLOSE_LONG,
	# 			"price": 11,  # 6
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_OPEN_SHORT,
	# 			"price": 11,
	# 		},
	# 		{
	# 			"action": Constants.ACTION_REVERSE_CLOSE_SHORT,
	# 			"price": 17,  # -12
	# 		},
	# 	]
	# 	result7 = Logic.calculate_rate(actions7)
	# 	self.assertEqual(result7["num_trade"], 1)
	# 	self.assertEqual(result7["reverse_num_trade"], 1)
	# 	self.assertEqual(result7["num_short"], 0)
	# 	self.assertEqual(result7["reverse_num_short"], 1)
	# 	self.assertEqual(result7["num_win"], 1)
	# 	self.assertEqual(result7["num_lose"], 2)
	# 	self.assertEqual(result7["win_amount"], -10)
	
	# def test_calculate_flunc_avg(self):
	# 	ls = self.get_data_from_test_csv("simple_test.csv")
	# 	self.assertEqual(Logic.calculate_flunc_avg(ls, 0), 3.0)

	def test_is_low_point(self):
		cd = SimpleNamespace()
		cd.open = 500
		cd.high = 500
		cd.low = 410
		cd.close = 440
		cd.direction = Constants.DIRECTION_DOWN
		cd.datetime = '2022-09-13 21:18:00'

		last_cd = SimpleNamespace()
		last_cd.open = 450
		last_cd.low = 440
		last_cd.high =510
		last_cd.close = 500
		last_cd.direction = Constants.DIRECTION_UP
		last_cd.datetime = '2022-09-13 21:17:00'
		self.assertTrue(Logic.is_low_point(Constants.DIRECTION_UP, last_cd, cd))


if __name__ == '__main__':
	unittest.main()