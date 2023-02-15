import os
from dotenv import load_dotenv
from peewee import *
from playhouse.postgres_ext import *

load_dotenv()

DATABASE = os.environ.get('NGSMGR_DATABASE', 'ngsmgr')
USERNAME = os.environ.get('NGSMGR_USERNAME', 'postgres')
PASSWORD = os.environ.get('NGSMGR_PASSWORD', '')
HOST = os.environ.get('NGSMGR_HOST', '127.0.0.1')
PORT = os.environ.get('NGSMGR_PORT', '5432')

database = PostgresqlExtDatabase(DATABASE, user=USERNAME, password=PASSWORD, host=HOST, port=PORT, register_hstore=True)

backend =os.environ.get('NGSMGR_BACKEND', 'local')

class BaseModel(Model):
    class Meta:
        database = database

# 实现乐观锁
class ConflictDetectedException(Exception): pass

class BaseVersionedModel(Model):
    version = IntegerField(default=1, index=True)

    class Meta:
        database = database

    def save_optimistic(self):
        if not self.id:
            # New Record
            return self.save()

        # Update any data that has changed and bump the version counter.
        field_data = dict(self.__data__)
        current_version = field_data.pop('version', 1)
        self._populate_unsaved_relations(field_data)
        field_data = self._prune_fields(field_data, self.dirty_fields)
        if not field_data:
            raise ValueError('No changes have been made.')

        ModelClass = type(self)
        field_data['version'] = ModelClass.version + 1   # Atomic increment

        query = ModelClass.update(**field_data).where(
                (ModelClass.version == current_version) &
                (ModelClass.id == self.id))
        if query.execute() == 0:
            # No rows were update, indicating another process has saved
            # a new version. How you handle this situation is up to you,
            # but for simplicity I'm just raising an exception
            raise ConflictDetectedException
        else:
            self.version += 1
            return True