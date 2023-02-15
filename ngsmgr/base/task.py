import os
from datetime import datetime
from peewee import *
from playhouse.postgres_ext import *

from ngsmgr.utils import config
from .analysis import Analysis
from .worker import Worker

class Task(config.BaseModel):
    analysis = ForeignKeyField(Analysis)
    cmdlist = BinaryJSONField(default={})
    shell = BooleanField(default=True)
    outdir = CharField(null=True)
    outs = BinaryJSONField(default={})
    parents = ArrayField(default=[])
    #callback = CharField(max_length=150, null=True)
    hooks = BinaryJSONField(default={}) # before_runing, after_running callback
    priority = IntegerField(default=1)
    resource = BinaryJSONField(default={'expect_cpus': 1, 'expect_mems': 1024*1024*1024}) # 1G
    status = CharField(default='submited')
    created = DateTimeField(default=datetime.now)
    started = DateTimeField(null=True)
    finished = DateTimeField(null=True)
    retried = DateTimeField(null=True)
    retries = IntegerField(default=0)
    expires = IntervalField(null=True)
    result = BinaryJSONField(default={})
    pid = IntegerField(null=True) # 进程id
    worker = ForeignKeyField(Worker,null=True)
    notes = BinaryJSONField(default={}, null=True)

    @staticmethod
    def ready_tasks():
        '''
        可以提交运行的任务
        '''
        sql = """
            SELECT id FROM task AS j 
            WHERE (parents = '{}' OR 
                    NOT EXISTS (
                        SELECT 1 FROM task 
                        WHERE id = ANY (j.parents) AND status != 'finished')
                    ) AND status = 'submit'
            ORDER BY priority DESC, created    
        """
        cursor = database.execute_sql(sql)
        task_ids = [ i[0] for i in cursor]
        return task_ids

    def add_task(self, cmdlist, outs, **kwargs):
        if 'analysis' not in kwargs:
            kwargs['analysis'] = self.analysis_id
        if 'shell' not in kwargs:
            if isinstance(cmdlist, list):
                kwargs['shell'] = False
        if 'outdir' not in kwargs:
            kwargs['outdir'] = self.outdir
        if 'parents' not in kwargs:
            kwargs['parents'] = [self.id]
        else:
            if isinstance(kwargs['parents'], int):
                kwargs['parents'] = [kwargs['parents'], self.id]
            if isinstance(kwargs['parents'], list):
                kwargs['parents'].append(self.id)

        t = Task.create(
                cmdlist = cmdlist,
                outs = outs,
                **kwargs
                )

        return t

    def add_qctl(self, metrics):
        return Qctl.create(task=self, metrics=metrics)

    def local_run(self):
        try:
            proc = subprocess.Popen(self.cmdlist,
                    shell=self.shell,
                    cwd=self.outdir,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
        except OSError:
            pass
        except ValueError:
            pass
        else:
            Task.update(status='running', 
                    started=datetime.now(), 
                    pid=proc.pid).where(Task.id == self.id).execute()

            # 
            stdouts, stderrs = proc.communicate()
            result = {
                    'stdout': stdouts,
                    'stderr': stderrs,
                    'returncode': proc.returncode
                    }

            if proc.returncode == 0:
                Task.update(status='finished', 
                        finished=datetime.now(),
                        result=result).where(Task.id == self.id).execute()
                if 'after_finished' in self.hooks:
                    pass
            elif proc.returncode < 0: 
                if self.retrues == 0:
                    retries = 1
                else:
                    retries = self.retries
                Task.update(status='failed', retries=retries).where(Task.id==self.id).execute()
            else:
                Task.update(status='failed').where(Task.id==self.id).execute()
                if 'after_failed' in self.hooks:
                    pass

    def slurm_run(self):
        submit_job = {
                'output': 'ngsmgr-%j.out',
                'error': 'ngsmgr-%j.err'
                }

        submit_job['work_dir'] = self.outdir
        
        if self.shell:
            submit_job['wrap'] = self.cmdlist
        else:
            submit_job['wrap'] = shlex.join(self.cmdlist)

        if mkey in self.resource:
            submit_job['mem'] = self.resource[mkey]
        if ckey in self.resource:
            submit_job['mincpus'] = self.resource[ckey]
        
        sbatch_cmdlist = ['sbatch',
                '--wrap', submit_job['wrap'],
                '--chdir', submit_job['work_dir'],
                '--output', submit_job['output'],
                '--error', submit_job['error'],
                '--mincpus', str(submit_job['mincpus']),
                '--mem', str(submit_job['mem'])]
            
        proc = subprocess.run(sbatch_cmdlist, capture_output=True, text=True)
        if proc.returncode == 0:
            slurm_jobid = int(proc.stdout.split()[-1])
            Task.update(status='running', 
                    started=datetime.now(), 
                    pid=slurm_jobid).where(Task.id==self.id).execute()
        else:
            pass


    def run(self):
        if (self.status == 'running'): return 
        if utils.files_exists(self.outs.values()) or Task.get_or_none(
                (Task.analysis == self.analysis) & 
                (Task.cmdlist.contains_all(self.cmdlist)) & 
                (Task.outdir == self.outdir) & 
                (Task.status == 'running')):
            Task.update(status = 'finished').where(Task.id == self.id).execute()
            return
        
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

        if self.worker.backend == 'local':
            self.local_run()
        elif self.worker.backend == 'slurm':
            self.slurm_run()
        return 
