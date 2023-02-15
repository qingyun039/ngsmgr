import os
import sys
import yaml
import json
import click
from importlib import import_module
from peewee import fn

from ngsmgr.base import Pipeline
from ngsmgr.utils.common import update_dict

BASEMOD = 'ngsmgr.workflow'

@click.group()
def pipeline():
    """流程的创建、更新及查看"""
    pass

@pipeline.command()
@click.argument('name')
@click.argument('config')
@click.option('--tag', default='default', help="流程的分支")
@click.option('--description', help='对流程的简要描述')
@click.option('--strict', default=False, help='检查流程模块是否可行')
def add(name, config, tag, description, strict):
    """为已有的流程模块指定默认的配置信息，即添加一个可用流程
    
    \b
    NAME: 流程模块名称
    CONFIG: 流程默认配置文件， yaml格式
    """
    if ':' in name:
        name, tag = name.split(':')
    mod = ':'.join([BASEMOD, name])
    try:
        with open(config) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        click.echo(f'读取配置文件({config})失败：{e}', err=True)
        sys.exit()

    if strict:
        try:
            workflow_mod = 'ngsmgr.workflow.' + name.lower()
            mod = import_module(workflow_mod)
        except Exception as e:
            click.echo(f'无法加载流程模块({mod}): {e}', err=True)
            sys.exit()
    
    version = 0
    if description is None:
        description = '没有描述'
    try:
        Pipeline.create(name=name, tag=tag, defaults=config, version=version, description=description)
    except Exception as e:
        click.echo(f'保存到数据库失败：{e}', err=True)
        sys.exit()

@pipeline.command()
@click.argument('name')
@click.argument('config')
@click.option('--tag', default='default', help="流程的分支")
@click.option('--description', help='对流程的简要描述')
def update(name, config, tag, description):
    """更新流程的默认配置信息
    
    \b
    NAME: 流程模块名称
    CONFIG: 流程默认配置文件， yaml格式文件或JSON字符串
    """
    if ':' in name:
        name, tag = name.split(':')
    if os.path.exists(config):
        try:
            with open(config) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            click.echo(f'读取配置文件({config})失败：{e}', err=True)
            sys.exit()
    else:
        try:
            config = json.loads(config)
        except Exception as e:
            click.echo(f'解析JSON字符串失败：{e}', err=True)

    latest = Pipeline.latest(name, tag=tag)
    new_config = update_dict(latest.defaults, config)
    new_version = latest.version + 1
    if description is not None:
        new_description = latest.description + '\n' + description
    else:
        new_description = latest.description
    
    try:
        Pipeline.create(name=name, tag=tag, defaults=new_config, version=new_version, description=new_description)
    except Exception as e:
        click.echo(f'更新默认配置失败：{e}', err=True)
        sys.exit()

@pipeline.command()
@click.option('--verbose', default=False, help="显示详细信息")
def list(verbose):
    '''列出所有流程'''

    if verbose:
        fields = ['name', 'tag', 'version', 'description', 'defaults']
        ps = Pipeline.select()
    else:
        fields = ['name', 'tag', 'description']
        # http://docs.peewee-orm.com/en/latest/peewee/relationships.html#subqueries
        latest_query = (Pipeline
                        .select(Pipeline.name, Pipeline.tag, fn.MAX(Pipeline.version).alias('latest_version'))
                        .group_by(Pipeline.name, Pipeline.tag)
                        .cte('latest_query', columns=['name', 'tag', 'latest_version']))
        predicate = ((Pipeline.name == latest_query.c.name) & 
                     (Pipeline.tag == latest_query.c.tag) &
                     (Pipeline.version == latest_query.c.latest_version))
        ps = (Pipeline
              .select(Pipeline.name, Pipeline.tag, Pipeline.description)
              .join(latest_query, on=predicate)
              .where(predicate)
              .with_cte(latest_query))

    click.echo("\t".join(fields))
    for row in ps:
        click.echo("\t".join([ str(getattr(row, i)) for i in fields ]))
    