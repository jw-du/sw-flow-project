1：看日历
* 调用[eastmoney-calendar]+ [bing_search]skill:搜索分析接下来几天是否有重磅会议（美联储议息、国内重要经济会议等）。
* 调用[bing_search]skill: 搜索分析是否刚发生过重磅冲突（地缘政治、关税冲突等），分析方式：例如搜索得出恰好处于地缘政治冲突后，资金通常不敢大举进攻，以避险需求为主

2：看外盘数据
* 调用[us-market-watch]skill : 看外盘：昨日美股纳斯达克、标普500涨跌幅，特别是中概股（KWEB/PGJ）和富时中国A50期指的表现。
* 调用[sina-forex] skill: 看汇率：昨日离岸人民币（USD/CNH）是升值还是贬值？分析：若贬值压力大，大盘难有大行情。

3：看中盘国内情绪
* 调用[bing_search]+[industry-keywords] skill: 搜索本周证监会、央行、发改委是否有重磅利好，官媒（证券时报、中证报）近期头版风向；行业新闻是否有重大事件或政策发布。并调用[industry-news-sentiment]skill进行分析。