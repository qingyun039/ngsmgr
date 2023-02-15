import os
from peewee import *
from playhouse.postgres_ext import *

DATABASE = os.environ.get('NGSMGR_DATABASE', 'test')
USERNAME = os.environ.get('NGSMGR_USERNAME', 'postgres')
PASSWORD = os.environ.get('NGSMGR_PASSWORD', '')
HOST = os.environ.get('NGSMGR_HOST', '127.0.0.1')
PORT = os.environ.get('NGSMGR_PORT', '5432')

db = PostgresqlExtDatabase(DATABASE, user=USERNAME, password=PASSWORD, host=HOST, port=PORT, register_hstore=True)
#db = SqliteDatabase(':memory:')

class BaseModel:
    class Meta:
        database = db

class Person(Model):
    name = CharField()
    birthday = DateField()

    class Meta:
        database = db
        table_name = 'ngsmgr_person'

class Pet(Model):
    owner = ForeignKeyField(Person, backref='pets')
    name = CharField()
    animal_type = CharField()

    class Meta:
        database = db
        table_name = 'ngsmgr_pet'

class Owner(Person):
    class Meta:
        table_name = 'ngsmgr_person'

    def run(self, params):
        print(self.name, self.birthday)
        for key, val in params.items():
            print(f"key: {key}\tvalue: {val}")

db.create_tables([Person, Pet])

from datetime import date

uncle_bob = Person(name='Bob', birthday=date(1969, 1, 15))
uncle_bob.save()

o = Owner.get(Owner.name == 'Bob')
o.run({'a':1, 'b':2, 'c':3})
