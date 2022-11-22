目前版本为S4，目录为s4,其中fixed_minute.py为右侧策略，minute.py为左侧策略，tick_test.py为模拟实盘测试脚本
统计昨日的d, Crmax, 方向延给今日开仓实例
出现有效突破，设置协定CR，协定CR上标注有tag=True为可以进行开仓
出现有效回归时，即回到协定CR中最近的满足指定长度的IR时进行开仓
开仓设置止损位为D，开仓后统计Irmax，并使用Irmax的起点作为平仓点，要求Irmax的长度需要大于10单位，并且方向跟开仓方向一致，即开多时，方向向上，开空时方向向下
开多时设置对应的tick价位-1单位，开空时对应tick价位+1单位

方向:
目前初始化方向为昨日结束方向延续，如果没有昨日方向，就使用最开始具有方向的分钟定初始值
刷新CRmax的时候，程序方向跟CRmax方向一致
当回到CRmax的起点时，程序方向跟CRmax方向相反
当回到CRmax的终点时，程序方向跟CRmax方向相同

cr:
相同方向的分钟数据列表，当新的一分钟跟list的方向不一致时，就重置cr
ir : 当前一分钟的幅度，如果跟上一分钟是连续的就加起来
max_ir_by_cr : 从cr中找出最大的ir
