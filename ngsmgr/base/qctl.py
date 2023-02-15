from peewee import *
from playhouse.postgres_ext import *

from ngsmgr.utils import config
from .task import Task

def cast_text(node):
    return NodeList((node, SQL('::text')), glue='')

class Qctl(config.BaseModel):
    task = ForeignKeyField(Task)
    metrics = BinaryJSONField()

    @staticmethod
    def sample_metrics(sample):
        #sql = f"SELECT id,cmdlist FROM qctl INNER JOIN task ON qctl.task_id = task.id WHERE task.cmdlist::text like '%{sample}%'"
        query = (Qctl
                .select()
                .join(Task)
                .where(cast_text(Task.cmdlist).regexp(sample)))

        metrics = {}
        for q in query:
            metrics.update(q.metrics)

        return metrics

    @staticmethod
    def qc_table(samples, fields):
        table = []
        for sample in samples:
            metrics = Qctl.sample_metrics(sample)
            selected = []
            for field in fields:
                if field in metrics:
                    selected.append(metrics[field])
                else:
                    selected.append(None)
            table.append(selected)

        return table