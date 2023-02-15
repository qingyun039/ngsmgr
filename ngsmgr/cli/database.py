import sys
import click

from ngsmgr.base import create_tables


@click.group()
def database():
    """后端数据库相关操作"""
    pass

@database.command()
def reset():
    """重置数据库"""
    if click.prompt("确定删除数据库中的所有内容？"):
        try:
            create_tables()
        except Exception as e:
            click.echo(f"重置失败：{e}")
            sys.exit()
        
        click.echo(f'重置成功！')