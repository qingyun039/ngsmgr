from ngsmgr.utils import config
from .analysis import Analysis
from .pipeline import Pipeline
from .task import Task
from .qctl import Qctl
from .worker import Worker


def create_tables():
    tables = [Worker, Pipeline, Analysis, Task, Qctl]
    with config.database:
        #all_tables = database.get_tables()
        config.database.drop_tables(tables)
        config.database.create_tables(tables)
        Pipeline.create_api_pipeline()