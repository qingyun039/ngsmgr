import os
import psutil
from ngsmgr.base import Worker

class Worker(Worker):

    @staticmethod
    def init_worker(resource=None):
        hostname = os.uname()[1]
        cpus = psutil.cpu_count()
        mems = psutil.virtual_memory().total
        max_queue = 50
        default_resource = {
                'total_cpus': cpus,
                'total_mems': mems,
                'max_queue': max_queue,
                }

        default_resource.update({
                'cpu_soft_rate': 0.90,
                'cpu_hard_rate': 0.99,
                'mem_soft_rate': 0.85,
                'mem_hard_rate': 0.95,
                })
        if resource is not None and isinstance(resource, dict):
            resource = dict(default_resource, **resource)
        else:
            resource = default_resource
        
        w = Worker.create(
                host = hostname,
                started = datetime.now(),
                active = True,
                backend = backend,
                resource = resource,
                )
        
        return w

    def terminate_worker(self):
        Worker.update(active=False, terminated=datetime.now()).where(Worker.id == self.id).execute()

    def dispatcher(self):
        mem_available = psutil.virtual_memory().available
        load_avg = psutil.getloadavg()
        cpu_persent = psutil.cpu_persent(0.2)

        task_ids = Task.ready_tasks()
        submit_tasks = []
        mem_remain = mem_available
        cpu_remain = load_avg
        for id in task_ids:
            task = Task.get_or_none(id)
            mem_remain -= task.resource[mkey]
            cpu_remain += task.resource[ckey] * cpu_persent
            if ((mem_remain / self.resource['total_mems'] < self.resource['mem_soft_rate']) and
            (cpu_remain / self.resource['total_cpus'] < self.resource['cpu_soft_rate'])):
                submit_tasks.append(task)
        

        return submit_tasks

    def check_running(self):
        for task in self.task_set.where(Task.status == 'running'):
            # 记录资源
            psinfo = psutil.Process(task.pid)
            meminfo = psinfo.memory_info()
            cpuinfo = psinfo.cpu_times()
            resource = {
                    'mem_rss': meminfo.rss,
                    'mem_vms': meminfo.vms,
                    'mem_shared': meminfo.shared, # only linux
                    'cpu_percent': psinfo.cpu_percent(),
                    'cpu_user': cpuinfo.user,
                    'cpu_system': cpuinfo.system,
                    'cpu_iowait': cpuinfo.iowait,
                    }
           
            for key in task.resource:
                if key in resource:
                    if task.resource[key] > resource[key]:
                        resource[key] = task.resource[key]
                else:
                    resource[key] = task.resource[key]

            if task.expires and (task.started + task.expires < datetime.now()):
                try:
                    os.kill(task.pid, 9)
                    note = "Killed by Worker: Time Expired"
                except:
                    note = "Time Expired: Kill Error"
                
                Task.update(resource=resource, status='failed', notes=note).where(Task.id == task.id).execute()
            else:
                Task.update(resource=resource).where(Task.id == task.id).execute()

    def check_exceed(self):
        load_avg = psutil.getloadavg()
        meminfo = psutil.virtual_memory()

        if ((meminfo.used / self.resource['total_mems'] > self.resource['mem_hard_rate']) or 
        (load_avg / self.resource['total_cpus'] > self.resource['cpu_hard_rate'])):
            # 本地运行资源过载
            pass

    def run_Task(self, task):
        Task.update(worker=self).where(Task.id == task.id).execute()
        task.run()
