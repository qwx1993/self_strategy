from cgi import print_form
import sys
from types import SimpleNamespace
import os
import copy
from datetime import datetime
from datetime import timedelta
from self_strategy.constants import Constants

class Logic:

	"""
	检测是否在振荡区间范围内，
	出现次数最多的高点，跟出现次数最多的低点间距为S
	"""
	def check_oscillating_interval(oscillating_interval_list):
		b_list = []
		high_price = 0
		high_number_max = 0
		low_price = 0
		low_number_max = 0
		for cd in oscillating_interval_list:
			high_number = 0
			low_number = 0
			for d in oscillating_interval_list:
				if d.high >= cd.high >= d.low:
					high_number += 1
				if d.high >= cd.low >= d.low:
					low_number += 1
			# 寻找最高点
			if high_number > high_number_max and high_number > 0:
				high_number_max = high_number
				high_price = cd.high
			elif high_number == high_number_max and high_number > 0:
				if cd.high > high_price:
					high_price = cd.high

			# 寻找最低点
			if low_number > low_number_max and low_number > 0:
				low_number_max = low_number
				low_price = cd.low
			elif low_number == low_number_max and low_number > 0:
				if cd.low < low_price:
					low_price = cd.low

		if high_price > 0 and low_price > 0:
			b_list.append(high_price)
			b_list.append(low_price)
			return True, abs(high_price - low_price), b_list, max(high_number_max, low_number_max)
		else:
			return False, None, [], 0

	"""
	是否已经完成突破
	"""

	def has_break_through(cd, b1_to_b2_interval):
		diff = cd.high - cd.low
		if diff >= Constants.MULTIPLE_OF_BREAKTHROUGH * b1_to_b2_interval:
			return True
		else:
			return False

	"""
	是否超出了A点涨跌幅度的范围
	"""

	def is_out_range(cd, reference_point_a_price, amplitude_ratio):
		if Logic.high_out_range(cd, reference_point_a_price, amplitude_ratio) \
				or Logic.low_out_range(cd, reference_point_a_price, amplitude_ratio):
			return True
		else:
			return False

	"""
	低点是否在A点的振荡范围内
	"""

	def low_out_range(cd, reference_point_a_price, amplitude_ratio):
		if abs(cd.low - reference_point_a_price) > reference_point_a_price * amplitude_ratio:
			return True
		else:
			return False

	"""
	高点是否在A点的振荡范围内
	"""

	def high_out_range(cd, reference_point_a_price, amplitude_ratio):
		if abs(cd.high - reference_point_a_price) > reference_point_a_price * amplitude_ratio:
			return True
		else:
			return False

	"""
	情况1判定
	开多是当前点的cd.high > 参考点D的high就开仓,开仓价为 reference_point_d.high
	开空是当前点的cd.low < 参考点D的low就开仓,开仓价为 reference_point_d.low
	"""

	def situation1(d2, breakthrough_direction, reference_point_d):
		if breakthrough_direction == Constants.DIRECTION_UP:
			if d2.high > reference_point_d.high:
				return True
			else:
				return False
		else:
			if d2.low < reference_point_d.low:
				return True
			else:
				return False

	"""
	情况一止损判断
	开多情况下，当前点的cd.close小于止损价就止损，止损价为stop_loss_ln_price
	开空情况下，当前点的cd.close大于stop_loss_ln_price就止损，止损价为stop_loss_ln_price
	"""

	def situation1_stop_loss(cd, stop_loss_ln_price, breakthrough_direction):
		if breakthrough_direction == Constants.DIRECTION_UP:
			if cd.low < stop_loss_ln_price:
				return True
			else:
				return False
		else:
			if cd.high > stop_loss_ln_price:
				return True
			else:
				return False

	"""
	情况2判定
	高于b1但是不超过d1
	"""

	def situation2(d2, breakthrough_direction, reference_point_d, b1_price):
		if breakthrough_direction == Constants.DIRECTION_UP:
			if reference_point_d.high >= d2.high and b1_price < d2.low:
				return True
			else:
				return False
		else:
			if reference_point_d.low <= d2.low and b1_price > d2.high:
				return True
			else:
				return False
	"""
	开多情况下如果b1_price大于d2的最低价就为真
	开空情况下如果b1_price小于d2的最高点为真
	"""
	def need_restart(d2, breakthrough_direction, b1_price):
		if breakthrough_direction == Constants.DIRECTION_UP:
			if b1_price > d2.low:
				return True
			else:
				return False
		else:
			if b1_price < d2.high:
				return True
			else:
				return False

	"""
	情况二开仓条件
	出现ln+1 > ln 并且 ln_dn_max出现最大值就开仓
	"""

	def situation2_open_a_position(cd, breakthrough_direction, stop_loss_ln_price, max_l_to_h):
		current_l_to_h = abs(cd.high - cd.low)
		if breakthrough_direction == Constants.DIRECTION_UP:
			if cd.low > stop_loss_ln_price and current_l_to_h > max_l_to_h:
				return True
			else:
				return False
		else:
			if cd.high < stop_loss_ln_price and current_l_to_h > max_l_to_h:
				return True
			else:
				return False

	"""
	情况二止损判断
	"""

	def situation2_stop_loss(cd, breakthrough_direction, ln_price):
		if breakthrough_direction == Constants.DIRECTION_UP:
			if cd.low < ln_price:
				return True
			else:
				return False
		else:
			if cd.high > ln_price:
				return True
			else:
				return False

	"""
	是否进入逆趋势
	逆趋势判断条件，统计整个过程的最大上涨幅度max_l_to_d_interval，如果当前下降幅度 > max_l_to_d_interval
	就进入逆趋势

	"""

	def is_counter_trend(cd, max_r, breakthrough_direction):
		r = Logic.max_amplitude_length(cd)
		if r > max_r and not Logic.is_same_direction(cd, breakthrough_direction):
			return True
		else:
			return False

	"""
	新的逆趋势判定
	"""
	def is_counter_trend1(max_l_to_d, max_r):
		if max_r is None or max_l_to_d is None:
			return False
		if max_r.length > max_l_to_d.length:
			return True
		else:
			return False

	"""
	是否为高点
	"""
	def is_high_point(direction, last_cd, cd):
		if direction == Constants.DIRECTION_UP:
			if cd.high > cd.open and cd.high > cd.close:
				# 已经测试
				return True

			if cd.direction == Constants.DIRECTION_DOWN and cd.open == cd.high:
				if  last_cd.close < cd.open:
					# 已测试
					return True
				if last_cd.direction == Constants.DIRECTION_DOWN and last_cd.low < last_cd.close and last_cd.close <= cd.open:
					# 已测试
					return True

				if last_cd.direction == Constants.DIRECTION_UP and last_cd.high == last_cd.close and last_cd.close <= cd.open:
					# 已经测试
					return True
				
				if last_cd.open == last_cd.close == last_cd.high > last_cd.low and last_cd.close <= cd.open:
					# 已经测试
					return True
		else:
			if cd.low < cd.close and cd.low < cd.open:
				# 已经测试
				return True
			if cd.direction == Constants.DIRECTION_UP and cd.open == cd.low:
				if last_cd.close > cd.open:
					# 已经测试
					return True
				if last_cd.direction == Constants.DIRECTION_DOWN and last_cd.low == last_cd.close and last_cd.close >= cd.open:
					# 已经测试
					return True
				
				if last_cd.direction == Constants.DIRECTION_UP and last_cd.high > last_cd.close and last_cd.close >= cd.open:
					# 已经测试
					return True
				
				if last_cd.open == last_cd.close == last_cd.low < last_cd.high and last_cd.close >= cd.open:
					# 已经测试
					return True

		return False

	"""
	是否为低点 待完成
	"""
	def is_low_point(direction, last_cd, cd):
		if direction == Constants.DIRECTION_UP:
			if cd.low < cd.open and cd.low < cd.close:
				# 已经测试
				return True

			if cd.direction == Constants.DIRECTION_UP and cd.open == cd.low:
				if  last_cd.close > cd.open:
					# 已测试
					return True
				if last_cd.direction == Constants.DIRECTION_UP and last_cd.high > last_cd.close and last_cd.close >= cd.open:
					# 已测试
					return True

				if last_cd.direction == Constants.DIRECTION_DOWN and last_cd.low == last_cd.close and last_cd.close >= cd.open:
					# 已经测试
					return True
				
				if last_cd.open == last_cd.close == last_cd.low > last_cd.high and last_cd.close >= cd.open:
					# 已经测试
					return True
		else:
			if cd.high > cd.close and cd.high > cd.open:
				# 已经测试
				return True
			if cd.direction == Constants.DIRECTION_DOWN and cd.open == cd.high:
				if last_cd.close < cd.open:
					# 已经测试
					return True
				if last_cd.direction == Constants.DIRECTION_UP and last_cd.high == last_cd.close and last_cd.close <= cd.open:
					# 已经测试
					return True
				
				if last_cd.direction == Constants.DIRECTION_DOWN and last_cd.low < last_cd.close and last_cd.close <= cd.open:
					# 已经测试
					return True
				
				if last_cd.open == last_cd.close == last_cd.high > last_cd.low and last_cd.close <= cd.open:
					# 已经测试
					return True

		return False

	"""
	判断当前方向是否跟突破后的方向一致
	在开多情况下，如果当前点是上涨就为True
	在开空情况下，如果当前点是下跌就为True
	"""
	def is_same_direction(breakthrough_direction, cd):
		if cd.close > cd.open and breakthrough_direction == Constants.DIRECTION_UP:
			return True
		elif cd.close < cd.open and breakthrough_direction == Constants.DIRECTION_DOWN:
			return True
		else:
			return False
	
	"""
	判断两点是否方向一致
	"""
	def is_same_direction_by_two_point(last_cd, cd):
		if last_cd.direction == cd.direction:
			return True
		else:
			return False

	"""
	止盈判断
	下降幅度大于max_r的时候
	分钟内不知道价格走势，最大的幅度为high到low
	"""

	def stop_surplus(cd, breakthrough_direction, max_r):
		if Logic.is_same_direction(cd, breakthrough_direction):
			decrease_range = Logic.amplitude_length(cd, breakthrough_direction)
		else:
			decrease_range = Logic.max_amplitude_length(cd)
		if decrease_range >= max_r:
			return True
		else:
			return False

	def amplitude_length(cd, breakthrough_direction):
		if breakthrough_direction == Constants.DIRECTION_UP:
			return abs(cd.high - cd.close)
		else:
			return abs(cd.low - cd.close)

	"""
	获取上涨幅度
	"""
	def amplitude_length_for_long(cd, breakthrough_direction):
		if breakthrough_direction == Constants.DIRECTION_UP:
			return abs(cd.low - cd.close)
		else:
			return abs(cd.high - cd.close)


	def max_amplitude_length(cd):
		return abs(cd.high - cd.low)
	
	"""
	是否为十字星，即open=close
	"""
	def is_crossing_starlike(cd):
		if cd.direction == Constants.DIRECTION_NONE:
			return True
		else:
			return False

	"""
	获取最大的下降幅度
	"""
	def max_down_for_long(cd):
		return max(abs(cd.start - cd.low), abs(cd.high -cd.close))
	"""
	获取最大的上涨幅度
	"""
	def max_up_for_short(cd):
		return max(abs(cd.start - cd.high), abs(cd.low -cd.close))

	"""
	根据方向获取最大的上涨长度
	"""
	def get_max_len_by_direction(cd):
		if cd.close > cd.open:
			return Logic.max_up_for_short(cd)
		else:
			return Logic.max_down_for_long(cd)

	"""
	将file文件的读取位置倒回去n行
	"""
	def revert_n_lines(n, file):
		pos = file.tell() - 1
		i = 0
		while i < n:
			while pos > 0 and file.read(1) != "\n":
				pos -= 1
				file.seek(pos, os.SEEK_SET)
			i += 1

	"""
	将file文件的最后n行删掉
	"""
	def truncate_last_n_lines(n, file):
		Logic.revert_n_lines(n, file)
		file.truncate(file.tell())

	"""
	reference时间和target时间的间隔是否在n分钟内
	"""
	def within_minutes(n, reference, target):
		reference_obj = datetime.strptime(reference, '%Y-%m-%d %H:%M:%S')
		target_obj = datetime.strptime(target, '%Y-%m-%d %H:%M:%S')
		diff = abs(reference_obj - target_obj).total_seconds() / 60
		if diff <= n:
			return True
		return False

	"""
	reference时间和target时间之间的间隔
	"""
	def diff_minutes(reference, target):
		reference_obj = datetime.strptime(reference, '%Y-%m-%d %H:%M:%S')
		target_obj = datetime.strptime(target, '%Y-%m-%d %H:%M:%S')
		diff = abs(reference_obj - target_obj).total_seconds() / 60
		return diff

	def real_diff_minutes(reference, target):
		reference_obj = datetime.strptime(reference, '%Y-%m-%d %H:%M:%S')
		target_obj = datetime.strptime(target, '%Y-%m-%d %H:%M:%S')
		diff = (reference_obj - target_obj).total_seconds() / 60
		return diff	

	"""
	计算最近的n分钟的波动之和
	:param n: 最近的n分钟
	:param ls: 价格信息的数组
	"""
	def flunc_sum_for_latest_n(n, ls):
		flunc_sum = 0
		l = len(ls)
		for i in range(l-n, l):
			flunc_sum += ls[i].flunc
		return flunc_sum

	"""
	将多个时间单位合并成一个
	"""
	def merge_multiple_time_units(prices):
		l = len(prices)
		if l == 0:
			return None
		if l == 1:
			return prices[0]
		merged = SimpleNamespace()
		merged.open = prices[0].open
		merged.close = prices[l-1].close
		merged.high = prices[0].high
		merged.low = prices[0].low
		merged.flunc = abs(prices[0].open - prices[l-1].close)
		for i in range(len(prices)):
			if prices[i].high > merged.high:
				merged.high = prices[i].high
			if prices[i].low < merged.low:
				merged.low = prices[i].low
		merged.direction = Logic.get_direction_value(merged.open, merged.close)
		merged.datetime = prices[i].datetime
		return merged

	        #     if Logic.need_merge(self.last_cd, cd):
            #     print(f"合并数据 => {cd}")
            #     prices = []
            #     prices.append(self.last_cd)
            #     prices.append(cd)
            #     self.last_cd = Logic.merge_multiple_time_units(prices)
            # else:
            #     self.last_cd = cd

	"""
	处理最后的一分钟，如果需要合并，就合并处理
	"""
	def handle_last_cd(last_cd, cd):
		if last_cd is not None and Logic.need_merge(last_cd, cd):
			prices = []
			prices.append(last_cd)
			prices.append(cd)
			last_cd = Logic.merge_multiple_time_units(prices)
			# print(f"合并数据 => {cd} {last_cd}")
		else:
			last_cd = cd
		return last_cd

	"""
	判断是否需要合并数据
	"""
	def need_merge(last_cd, cd):
		if cd.direction == Constants.DIRECTION_UP:
			if not cd.open == cd.low or not cd.high == cd.close:
				return False
		elif cd.direction == Constants.DIRECTION_DOWN:
			if not cd.open == cd.high or not cd.low == cd.close:
				return False

		if cd.direction == Constants.DIRECTION_UP:
			if last_cd.direction == Constants.DIRECTION_UP:
				if last_cd.high == last_cd.close and cd.open >= last_cd.close:
					return True
			elif last_cd.direction == Constants.DIRECTION_DOWN:
				if last_cd.close > last_cd.low and cd.open >= last_cd.close:
					return True
		elif cd.direction == Constants.DIRECTION_DOWN:
			if last_cd.direction == Constants.DIRECTION_UP:
				if last_cd.high > last_cd.close and cd.open <= last_cd.close:
					return True
			elif last_cd.direction == Constants.DIRECTION_DOWN:
				if last_cd.low == last_cd.close and cd.open <= last_cd.close:
					return True

		return False

	"""
	根据目标时间获取指定前后的时间
	"""
	def get_date_str(obj_data_str, day):
		return (obj_data_str+timedelta(days=day)).strftime("%Y%m%d")

	"""
	判断当前时间是否为当天收盘前的最后一分钟，如果是，需要主动平掉所有仓，因为目前的策略只做日内交易
	"""
	def is_last_minute(datetime_str):
		datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
		# 从2016年开始当天收盘时间是下午15:00，之前是下午15:15
		if datetime_obj.year < 2016:
			if datetime_obj.hour == 15 and datetime_obj.minute == 15:
				return True
		else:
			if datetime_obj.hour == 15 and datetime_obj.minute == 0:
				return True
		return False
	
	"""
	判断当前时间是否为当天开盘前的第一分钟
	"""
	def is_realtime_start_minute(datetime_str):
		datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
		if datetime_obj.hour == 9 and datetime_obj.minute == 0:
			return True
		
		if datetime_obj.hour == 21 and datetime_obj.minute == 0:
			return True
		return False

	"""
	判断当前时间是否为当天开盘前的第一分钟
	"""
	def is_start_minute(datetime_str):
		datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
		if datetime_obj.hour == 9 and datetime_obj.minute == 1:
			return True
		
		if datetime_obj.hour == 21 and datetime_obj.minute == 1:
			return True
		return False

	"""
	判断是否为实盘时间，如果是就重置
	"""
	def is_firm_offer_start_minute(datetime_str):
		datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
		if datetime_obj.hour == 21 and datetime_obj.minute == 0:
			return True
		return False

	"""
	将csv数据文件中的一行数据转变成一个时间单位的价格信息object
	"""
	def raw_to_data_object(temp_array, line_count, raw_string):
		opening_price = float(temp_array[1])
		closing_price = float(temp_array[4])
		high = float(temp_array[2])
		low = float(temp_array[3])

		current = SimpleNamespace()
		current.datetime = temp_array[0]
		current.flunc = round(abs(closing_price - opening_price), 2)
		current.open = opening_price
		current.close = closing_price
		current.high = high
		current.low = low
		current.line = line_count

		current.raw_string = raw_string

		return current
	
	"""
	将csv数据文件中的一行数据转变成一个时间单位的价格信息object
	order_book_id,datetime,open,high,low,close
	SA2301,2022-08-26 21:01:00,2420.0,2424.0,2413.0,2415.0
	"""
	def history_price_to_data_object(temp_array, raw_string):
		opening_price = float(temp_array[2])
		closing_price = float(temp_array[5])
		high = float(temp_array[3])
		low = float(temp_array[4])

		current = SimpleNamespace()
		current.datetime = temp_array[1]
		current.flunc = round(abs(closing_price - opening_price), 2)
		current.open = opening_price
		current.close = closing_price
		current.high = high
		current.low = low
		current.direction = Logic.get_direction_value(opening_price, closing_price)

		current.raw_string = raw_string

		return current
	
	"""
	获取方向值
	"""
	def get_direction_value(opening_price, closing_price):
		if closing_price > opening_price:
			return Constants.DIRECTION_UP
		elif closing_price < opening_price:
			return Constants.DIRECTION_DOWN
		else:
			return Constants.DIRECTION_NONE

	
	"""
	将barData数据转变成一个时间单位的价格信息object
	"""
	def bar_to_data_object(bar):
		opening_price = float(bar.open_price)
		closing_price = float(bar.close_price)
		high = float(bar.high_price)
		low = float(bar.low_price)

		current = SimpleNamespace()
		current.datetime = bar.datetime.strftime("%Y-%m-%d %H:%M:%S")
		current.flunc = round(abs(closing_price - opening_price), 2)
		current.open = opening_price
		current.close = closing_price
		current.high = high
		current.low = low
		current.direction = Logic.get_direction_value(opening_price, closing_price)
		
		return current
	
	"""
	将barData转成一行的字符串
	"""
	def format_bar_data_to_line(bar):
		format_time = bar.datetime.strftime("%Y-%m-%d %H:%M:%S")
		line = f"{format_time},{bar.open_price},{bar.high_price},{bar.low_price},{bar.volume},{bar.open_interest},{bar.turnover}";
		
		return line

	"""
	处理包含最近的一系列时间单位的价格信息的数组latest_f, 返回4个值
	其中1个值是除了这3个单位以外，之前的最近的一个下跌的时间单位的价格低点
	另3个值包含最近的连续3个时间单位的价格信息
	"""
	def nearest_fall_and_consecutive_3(latest_f):
		latest_f_list = list(copy.deepcopy(latest_f))
		l = len(latest_f_list)
		excluded = latest_f_list[0:l-3]
		consecutive_3 = latest_f_list[l-3:l]
		nearest_fall = None
		for temp in reversed(excluded):
			if temp.close < temp.open:
				nearest_fall = temp
				break
		return nearest_fall, consecutive_3[0], consecutive_3[1], consecutive_3[2]

	"""
	计算AVG_FLUNC_LENGTH个时间单位的平均波动的3倍值
	"""
	def calculate_flunc_avg(prices, start_index):
		sum = 0
		count = start_index
		while count < (start_index + Constants.AVG_FLUNC_LENGTH):
			sum += prices[count].flunc
			count += 1
		return Constants.AVG_MULTIPLIER * (sum / float(Constants.AVG_FLUNC_LENGTH))

	"""
	返回加速上涨的相关参数，包括
	* 是否是加速上涨
	* 三次宽幅上涨中最小的波动
	* 第三次宽幅上涨的价格信息
	* 该次加速上涨的时间单位长度
	"""
	def confirmed_rise_params(min_flunc, latest_speeding, current_speeding_length):
		params = SimpleNamespace()
		params.min_flunc_for_speeding = min_flunc
		params.latest_speeding = latest_speeding
		params.current_speeding_length = current_speeding_length
		params.is_rise_speeding = True
		return params

	def speed_rise_with_params(rs, t1, t2, t3, t_last, possible_length):
		l = len(rs)
		multiplied_avg = Logic.calculate_flunc_avg(rs, l - (Constants.AVG_FLUNC_LENGTH + possible_length)) # 近10次波动的平均值的3倍
		if t1.close > t1.open and t1.flunc > multiplied_avg:
			if t2.close > t2.open and t2.flunc > t1.flunc:
				if t3.close > t3.open and t3.flunc > t2.flunc and t_last.close > t_last.open:
					return Logic.confirmed_rise_params(min(t1.flunc, t2.flunc, t3.flunc), t3, possible_length)
		return Logic.negative_rise_params()

	"""
	判断下跌观察点/上涨加速阶段
	rs是一个包含了过去 REFERENCE_AND_SPEEDING_LENGTH 个时间单位的如下信息的数组
	* datetime(时间)
	* open(开始值 opening_price)
	* close(结束值 closing_price)
	* flunc(波动值)
	"""
	def validate_rise_speeding(rs):
		l = len(rs)
		if l < Constants.REFERENCE_AND_SPEEDING_LENGTH:
			return Logic.negative_rise_params()

		current_minute = datetime.strptime(rs[l-1].datetime, '%Y-%m-%d %H:%M:%S') # 当前时间单位
		previous_minute = datetime.strptime(rs[l-2].datetime, '%Y-%m-%d %H:%M:%S') # 前一个时间单位
		if current_minute.date() != previous_minute.date(): # 当前时间单位是这一天开盘的第1分钟
			avg = Logic.calculate_flunc_avg(rs, l - (Constants.AVG_FLUNC_LENGTH + Constants.POSSIBLE_SPEEDING_0)) # 前一天收盘前最后10分钟的平均波动的3倍
			first_of_current_day = rs[l-1]
			last_of_previous_day = rs[l-2]
			if first_of_current_day.open > (avg + last_of_previous_day.close) and first_of_current_day.close > first_of_current_day.open:
				return Logic.confirmed_rise_params(first_of_current_day.flunc, first_of_current_day, Constants.POSSIBLE_SPEEDING_0)

		# 除去前面10分钟的参考波动时间以外，加速上涨的过程有可能是3分钟、4分钟或者5分钟
		# 首先检查加速上涨是3分钟的情况，也就是3分钟连续涨并且从第二分钟开始每分钟的波动都较前一分钟更大
		t1, t2, t3 = [rs[i] for i in (l - 3, l - 2, l - 1)]
		rise_params = Logic.speed_rise_with_params(rs, t1, t2, t3, t3, Constants.POSSIBLE_SPEEDING_1)
		if rise_params.is_rise_speeding:
			return rise_params

		# 然后检查加速上涨是4分钟的情况，也就是涨、(涨、跌)、涨，或者涨、(跌、涨)、涨
		t1, t2, t3, t_last = [rs[i] for i in (l - 4, l - 3, l - 2, l - 1)]
		t2 = Logic.merge_multiple_time_units([t2, t3])
		t3 = t_last
		rise_params = Logic.speed_rise_with_params(rs, t1, t2, t3, t_last, Constants.POSSIBLE_SPEEDING_2)
		if rise_params.is_rise_speeding:
			return rise_params

		# 最后检查加速上涨是5分钟的情况，也就是涨、(涨、跌)/(跌、涨)、(跌、涨)
		t1, t2, t3, t4, t_last = [rs[i] for i in (l - 5, l - 4, l - 3, l - 2, l - 1)]
		t2 = Logic.merge_multiple_time_units([t2, t3])
		t3 = Logic.merge_multiple_time_units([t4, t_last])
		rise_params = Logic.speed_rise_with_params(rs, t1, t2, t3, t_last, Constants.POSSIBLE_SPEEDING_3)
		if rise_params.is_rise_speeding:
			return rise_params

		return Logic.negative_rise_params()

	def speed_fall_finished(ls, t1, t2, t3, t_last):
		l = len(ls)
		if t2.close < t2.open and t2.close < t1.low:
			if t3.close < t3.open and t3.close < t2.low and t_last.close < t_last.open:
				return True
		return False

	"""
	判断是否发生了第一次宽幅下跌，第一次宽幅下跌发生即开空
	"""
	def validate_1st_fall_speeding(ls):
		l = len(ls)
		if l < Constants.AVG_FLUNC_LENGTH + 1:
			return False

		# 判断当天开盘第1分钟是否宽幅下跌，如果是，则开空
		current_minute = datetime.strptime(ls[l-1].datetime, '%Y-%m-%d %H:%M:%S') # 当前时间单位
		previous_minute = datetime.strptime(ls[l-2].datetime, '%Y-%m-%d %H:%M:%S') # 前一个时间单位
		if current_minute.date() != previous_minute.date(): # 当前时间单位是这一天开盘的第1分钟
			multiplied_avg = Logic.calculate_flunc_avg(ls, l - (Constants.AVG_FLUNC_LENGTH + Constants.POSSIBLE_SPEEDING_0)) # 前一天收盘前最后10分钟的平均波动的3倍
			first_of_current_day = ls[l-1]
			last_of_previous_day = ls[l-2]
			if first_of_current_day.open < (last_of_previous_day.close - multiplied_avg) and first_of_current_day.close < first_of_current_day.open:
				# 当天开盘的第1分钟是下跌的，并且该第1分钟的开盘价大于（前一天收盘前最后10分钟的平均波动的3倍 + 前一天最后的收盘价）
				# 则当天的该第1分钟算作第1次宽幅下跌
				ls[l-1].open_short_for_1st_fall = True
				return True

		multiplied_avg = Logic.calculate_flunc_avg(ls, l - (Constants.AVG_FLUNC_LENGTH + 1)) # 近10次破洞的平均值的3倍
		t1 = ls[l-1]
		if t1.close < t1.open and t1.flunc > multiplied_avg:
			ls[l-1].open_short_for_1st_fall = True
			return True
		return False

	"""
	超过最大幅度的起始价就改变方向、重置max_amplitude,R,r,rrn,max_r
	"""
	def is_exceed_max_amplitude_start_price(direction, max_amplitude, cd):
		if direction == max_amplitude.direction:
			if direction == Constants.DIRECTION_UP:
				if cd.low < max_amplitude.start:
					return True
			elif direction == Constants.DIRECTION_DOWN:
				if cd.high > max_amplitude.start:
					return True
			return False	

	"""
	超过最大幅度的起始价格改变方向后，又重新回落到最大幅度的结束价格后改变方向
	""" 
	def is_exceed_max_amplitude_end_price(direction, max_amplitude, cd):
		if not direction == max_amplitude.direction:
			if direction == Constants.DIRECTION_UP:
				if cd.low < max_amplitude.end:
					return True
			elif direction == Constants.DIRECTION_DOWN:
				if cd.high > max_amplitude.end:
					return True
		return False
	
	"""
	判断当前方向是否跟突破后的方向一致
	在开多情况下，如果当前点是上涨就为True
	在开空情况下，如果当前点是下跌就为True
	"""
	def is_same_breakthrough_direction(cd, breakthrough_direction):
		if cd.direction == breakthrough_direction:
			return True
		return False

	"""
	计算胜率和赔率
	"""
	def calculate_rate(actions_list, filename):
		num_trade = 0
		reverse_num_trade = 0
		num_short = 0
		reverse_num_short = 0
		num_win = 0
		num_lose = 0
		num_close_short = 0
		num_close_long = 0
		win_amount = 0 # 赢钱/数钱的具体值
		open_long_list = []  # 开多
		open_reverse_long_list = [] # 逆开多
		open_loss_list = []  # 开空
		open_reverse_loss_list = []  # 逆开空
		statistic_day = None
		temp_file = open("temp/line-chart-" + filename, "w+")
		for i in actions_list:
			current_day = datetime.strptime(i["datetime"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
			if statistic_day == None:
				statistic_day = current_day
			if statistic_day != current_day:
				# 之前的总数
				before_day_total_price = win_amount
				temp_file.write(str(statistic_day) + "," + str(before_day_total_price) + "\n")
				statistic_day = current_day

			temp_price = i["price"]
			current_action = i["action"]
			if current_action == Constants.ACTION_OPEN_LONG:  # 开多动作
				num_trade += 1
				open_long_list.append(temp_price)
			elif current_action == Constants.ACTION_CLOSE_LONG:  # 平多动作
				if len(open_long_list) < 1:
					print("开多 => 需要检查数据")
					continue
				open_long_price = open_long_list.pop()
				if temp_price > open_long_price:
					num_win += 1
					win_amount += abs(temp_price - open_long_price)
				else:
					num_lose += 1
					win_amount -= abs(temp_price - open_long_price)
			elif current_action == Constants.ACTION_OPEN_SHORT:  # 开空
				num_short += 1
				open_loss_list.append(temp_price)
			elif current_action == Constants.ACTION_CLOSE_SHORT:
				if len(open_loss_list) < 1:
					print("开空 => 需要检查数据")
					continue
				open_close_price = open_loss_list.pop()
				if temp_price < open_close_price:
					num_win += 1
					win_amount += abs(temp_price - open_close_price)
				else:
					num_lose += 1
					win_amount -= abs(temp_price - open_close_price)
			elif current_action == Constants.ACTION_REVERSE_OPEN_LONG:  # 逆趋势开多
				reverse_num_trade += 1
				open_reverse_long_list.append(temp_price)
			elif current_action == Constants.ACTION_REVERSE_CLOSE_LONG:
				if len(open_reverse_long_list) < 1:
					print("逆趋势开多 => 需要检查数据")
					continue
				open_reverse_long_price = open_reverse_long_list.pop()
				if temp_price > open_reverse_long_price:
					num_win += 1
					win_amount += 2 * abs(temp_price - open_reverse_long_price)
				else:
					num_lose += 1
					win_amount -= 2 * abs(temp_price - open_reverse_long_price)
			elif current_action == Constants.ACTION_REVERSE_OPEN_SHORT:  # 逆趋势开空
				reverse_num_short += 1
				open_reverse_loss_list.append(temp_price)
			elif current_action == Constants.ACTION_REVERSE_CLOSE_SHORT:
				if len(open_reverse_loss_list) < 1:
					print("逆趋势开空 => 需要检查数据")
					continue
				open_reverse_close_price = open_reverse_loss_list.pop()
				if temp_price < open_reverse_close_price:
					num_win += 1
					win_amount += 2 * abs(temp_price - open_reverse_close_price)
				else:
					num_lose += 1
					win_amount -= 2 * abs(temp_price - open_reverse_close_price)

		temp_file.write(str(statistic_day) + "," + str(win_amount) + "\n")
		temp_file.close()
		print("开多次数: " + str(num_trade) + ",\n开空次数: " + str(num_short) + ",\n逆趋势开多: " + str(reverse_num_trade) + ",\n逆趋势开空: " + str(reverse_num_short) + ",\n胜利次数: " + str(num_win)  + ",\n失败次数: " + str(num_lose) + ",\n赚取总金额: " + str(win_amount))
		return {
			"num_trade": num_trade,
			"num_short": num_short,
			"reverse_num_trade": reverse_num_trade,
			"reverse_num_short": reverse_num_short,
			"num_win": num_win,
			"num_lose": num_lose,
			"win_amount": win_amount,
		}