import sys
import click

from ngsmgr.base import Pipeline
from ngsmgr.utils.config import database
from ngsmgr.utils.common import dynamic_load
from ngsmgr.workflow.base  import BaseWorkflow

@click.group()
def analysis():
    pass

@analysis.command()
@click.argument('name')
@click.argument('config')
@click.option('--debug', is_flag=True)
def run(name, config, debug):
    """运行流程
    
    \b
    NAME: 流程模块名称
    CONFIG: 流程运行配置文件， yaml格式文件或JSON字符串
    """
    tag = 'default'
    if ':' in name:
        name, tag = name.split(':')
    
    pipeline = Pipeline.latest(name, tag=tag)

    # Search Workflow module
    workflow_class = 'ngsmgr.workflow.' + name.lower() + ':' + name
    Workflow = dynamic_load(workflow_class)
    if not issubclass(Workflow, BaseWorkflow):
        click.echo(f"不是一个符合的流程模块：{name}")
        sys.exit()

    workflow = Workflow(config=config, pipeline=pipeline)
    print(workflow.config)
    with database.atomic() as txn:
        workflow.run()