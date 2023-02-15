### 安装postgresql
```
yay -S postgresql
sudo su - postgres -c "initdb --locale en_US.UTF-8 -D '/var/lib/postgres/data'"
```
### 创建数据库
```
createdb -U postgres ngsmgr
```
### 安装psycopg2
```
pip install psycopy2
```
### 安装数据库扩展
```
psql -U postgres ngsmgr
CREATE EXTENSION hstore
```
