# final_django

基于python3的django的后端实现，要运行项目，执行以下命令：
```
pip install -r requirements.txt # 初始化依赖
python manage.py runserver 8080 # 指定在本地8080端口运行
```
所连接的数据库后端在`final_django/views/commons.py`中编辑

### 升级 2022.03.15

neo4j版本升级: 3.5.8->4.4.4，以支持traceback_check，导致py2neo的接口和返回值整体变化较大，一些原有涉及到py2neo的逻辑现在还未更新而无法使用
