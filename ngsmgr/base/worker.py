# 分离backend： 只实现local backend， 其它分离实现
#
import os
import psutil
from datetime import datetime
from peewee import *
from playhouse.postgres_ext import *

from ngsmgr.utils import config

class Worker(config.BaseModel):
    host = CharField()
    started = DateTimeField(default=datetime.now)
    terminated = DateTimeField(null=True)
    active = BooleanField(default=True)
    backend = CharField(max_length=50)
    resource = BinaryJSONField(default={})

