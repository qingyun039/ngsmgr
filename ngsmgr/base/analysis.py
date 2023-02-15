from datetime import datetime
from peewee import *
from playhouse.postgres_ext import *

from ngsmgr.utils import config
from .pipeline import Pipeline

class Analysis(config.BaseModel):
    pipeline = ForeignKeyField(Pipeline)
    params = BinaryJSONField(default={})
    created = DateTimeField(default=datetime.now)
    finished = DateTimeField(null=True)
    status = CharField(default='created')
    notes = BinaryJSONField(default={})

    def get_statu(self):
        '''
        返回本次分析各状态任务的数量：submit/running/finished/failed => 120/20/100/0
        '''
        rt = {'submit':0, 'running':0, 'failed':0, 'finished':0}
        query = Task.select(Task.status, fn.Count(Task.id).alias('count')).where(Task.analysis_id == self.id).group_by(Task.status)
        for q in query:
            rt[q.status] = q.count
        return rt

    def is_finished(self):
        '''
        判断该分析是否完成
        '''
        status = self.get_statu()
        if status['submit'] == 0 and status['running'] == 0 and status['failed'] == 0 and status['finished'] != 0:
            return True
        else:
            return False

    def is_failed(self):
        '''判断分析是否失败'''
        status = self.get_statu()
        if status['failed'] > 0:
            return True
        else:
            return False

    def is_running(self):
        status = self.get_statu()
        if status['failed'] == 0 and status['running'] > 0:
            return True
        else:
            return False

    def update_statu(self):
        if self.status == 'submit':
            if self.pipeline_id == 0: # pipeline api
                pass
        elif self.status == 'created' or self.status == 'running':
            if self.is_failed():
                Analysis.update(status = 'failed').where(Analysis.id == self.id).execute()
            elif self.is_finished():
                Analysis.update(status = 'finished').where(Analysis.id == self.id).execute()
            else:
                Analysis.update(status = 'running').where(Analysis.id == self.id).execute()
        elif self.status == 'finished':
            pass
        elif self.status == 'failed':
            pass


    @staticmethod
    def get_status(ids=None, recent=None, running=None):
        '''获取指定分析的状态'''
        if ids:
            ids = list(ids)
            query = (Analysis
                    .select(Analysis.id, Task.status, fn.Count(Task.id).alias('count'))
                    .where(Analysis.id << ids)
                    .join(Task, JOIN.LEFT_OUTER)
                    .group_by(Analysis.id, Task.status))
        elif running:
            query = (Analysis
                    .select(Analysis.id, Task.status, fn.Count(Task.id).alias('count'))
                    .where(Analysis.status != 'finished')
                    .join(Task, JOIN.LEFT_OUTER)
                    .group_by(Analysis.id, Task.status))
        else:
            if not isinstance(recent, int):
                recent = 3
            query = (Analysis
                    .select(Analysis.id, Task.status, fn.Count(Task.id).alias('count'))
                    .limit(recent)
                    .join(Task, JOIN.LEFT_OUTER)
                    .group_by(Analysis.id, Task.status))

        status = {}
        for q in query:
            if q.id not in status:
                status[q.id] = {}
            status[q.id][q.task.status] = q.count
        
        for i in status:
            for s in 'submit running failed finished'.split():
                if s not in status[i]:
                    status[i][s] = 0

        return status
