import click
from .analysis import analysis
from .pipeline import pipeline
from .database import database

@click.group()
def cli():
    pass

cli.add_command(pipeline)
cli.add_command(analysis)
cli.add_command(database)