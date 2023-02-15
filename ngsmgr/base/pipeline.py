from peewee import *
from playhouse.postgres_ext import *

from ngsmgr.utils import config

class Pipeline(config.BaseModel):
    name = CharField(max_length=150)
    tag = CharField(default='default')
    version = IntegerField(default=0)
    defaults = BinaryJSONField(default={})
    description = TextField(null=True)

    class Meta:
        indexes = (
            (('name', 'tag', 'version'), True),
        )

    @staticmethod
    def create_api_pipeline():
        p = Pipeline.create(
                id=0, 
                tag='default', 
                name='__pipeline__', 
                version=0, 
                defaults={}, 
                description='用做接口')
        return p

    @staticmethod
    def latest(name, tag='default'):
        '''获取最新的流程'''
        latest = (Pipeline
                 .select()
                 .where((Pipeline.name == name) & (Pipeline.tag == tag))
                 .order_by(Pipeline.version.desc())
                 .get())

        return latest