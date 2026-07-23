# FindGithubOpenComment
抓取指定星数区间仓库的所有正打开的issue并持久化到本地。
# 快速开始
## 运行环境
```shell
.\test_env\Scripts\activate
```
成功后shell命令行应该在前面显示(test_env)
```shell
(test_env) PS E:\find>
```
## 运行爬虫脚本
```shell
(test_env) PS E:\find>python find.py
```
抓取到每个仓库的正打开issue的全部comments才保存到found目录下
## 数据清洗
```shell
(test_env) PS E:\find>python clean.py
```
清洗后的数据同样放在found目录下.
