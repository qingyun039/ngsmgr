from ngsmgr.base import Worker

class SlurmWorker(Worker):
    @staticmethod
    def init_worker(resource=None):
        pass

    def dispatcher(self):
        num_queue = 0
        task_ids = Task.ready_tasks()
        submit_tasks = []
        for job in pyslurm.job().find_user(os.getlogin()).values():
            if job['job_state'] != 'COMPLETED':
                num_queue += 1
        n = self.resource['max_queue'] - num_queue
        if n > 0:
            for task_id in task_ids[:n]:
                submit_tasks.append(Task.get_by_id(task_id))
        return submit_tasks

    def check_running(self):
        running_tasks = {}
        for task in self.tast_set.where(Task.status == 'running'):
            slurm_jobid = task.pid
            running_tasks[slurm_jobid] = task

        slurm_jobids = list(running_tasks)
        slurmdb_jobs = pyslurm.slurmdb_jobs().get(jobids=slurm_jobids)
        for slurm_jobid in slurm_jobids:
            slurmdb_job = slurmdb_jobs[slurm_jobid]
            task = running_tasks[slurm_jobid]

            stdout_file = os.path.join(slurmdb_job['work_dir'], 'ngsmgr-'+str(slurm_jobid)+'.out')
            stderr_file = os.path.join(slurmdb_job['work_dir'], 'ngsmgr-'+str(slurm_jobid)+'.err')

            try:
                with open(stdout_file) as out, open(stderr_file) as err:
                    stdouts = out.readlines()
                    stderrs = err.readlines()
                # remove slurm stdout and stderr file
            except:
                stdouts = f'FileNoFound: {stdout_file}'
                stderrs = f'FileNoFound: {stderr_file}'
            
            result = {
                    'stdout': stdouts,
                    'stderr': stderrs,
                    'returncode': slurmdb_job['exitcode']
                    }
            
            if slurmdb_job['state_str'] == 'COMPLETED':
                resource = task.resource
                job_tres = slurm_job_tres(slurmdb_job)
                resource.update(job_tres)

                Task.update(status='finished', 
                        finished=datetime.now(), 
                        result=result, 
                        resource=resource).where(Task.id == task.id).execute()

                if 'after_finished' in task['hooks']:
                    pass
            
            elif slurmdb_job['state_str'] == 'FAILED':
                Task.update(status='failed',
                        result=result).where(Task.id == task.id).execute()

                if 'after_failed' in task.hooks:
                    pass
            
            elif slurmdb_job['state_str'] == 'RUNNING':
                if task.expires and (task.started + task.expires < datetime.now()):
                    rt = pyslurm.slurm_kill_job(slurm_jobid, 9)
                    if rt == 0:
                        note = "Killed by Worker: Time Expired"
                    else:
                        note = "Time Expired: Kill Error"
                
                Task.update(status='failed', notes=note).where(Task.id == task.id).execute()