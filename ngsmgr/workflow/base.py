import os
import abc
import copy
import yaml
import collections.abc
from addict import Dict
from importlib import import_module
from inspect import signature, isfunction
from ngsmgr.modules.inline import Cmdline
from ngsmgr.base import Pipeline, Analysis, Task
from ngsmgr.errors import PipelineError, WorkflowError, AnalysisConfigError

class Scatter:
    """任务分发器"""
    def __init__(self, mn=None, data=None, keygen=None):
        self.manager = mn
        self.rawdata = data
        self.keygen = keygen
        if data and keygen:
            self.pdata = melt_dset(data, **keygen)  # packer data 

    def __getattr__(self, name):
        if hasattr(self.manager, name):
            return self.manager.name
        else:
            raise AttributeError()


class BaseWorkflow:
    """流程构建基类"""
    # 流程默认参数
    defaults = {}

    # 流程使用到的命令模块
    modules = {}

    def __init__(self, config=None, analysis=None, pipeline=None):
        """构建函数"""
        # 输入的配置
        if config is None:
            config = {}
        elif isinstance(config, str):
            if os.path.exists(config):
                try:
                    with open(config) as f:
                        config = yaml.safe_load(f)
                except Exception as e:
                    raise AnalysisConfigError(f'读取配置文件({config})失败：{e}')
            else:
                try:
                    config = json.loads(config)
                except Exception as e:
                    raise AnalysisConfigError(f'解析JSON字符串失败：{e}')
        elif isinstance(config, dict):
            pass
        else:
            raise AnalysisConfigError(f"{config}需要是yaml文件或字典")

        # 保存在数据库中的配置
        if pipeline is None:
            pipeline = Pipeline.latest(self.__class__.__name__)
            if pipeline is None:
                raise PipelineError("Pipeline不存在")
        self.pipeline = pipeline
        if not hasattr(self.pipeline, 'defaults'):
            raise PipelineError("Pipeline配置危险")
        
        # 配置
        self.config = {}
        for d in (self.defaults, self.pipeline.defaults, config):
            update_dict(self.config, d)
        self.config = Dict(self.config)
        self.config.prefix = 'test' # 流程输出前缀

        self.analysis = analysis or Analysis.create(pipeline=self.pipeline)

        self.p = None

        self._modules = {}
        for m in self.modules:
            self.decorate_module(m)

        self._scatter = False
        self._scatter_data = None
        self._deps = {}

    def __getattr__(self, name):
        if name in self._modules:
            return self._modules[name]
        else:
            raise WorkflowError("命令模块不存在")

    @abc.abstractmethod
    def run(self):
        """generate workflow"""
        raise NotImplementedError
    
    @abc.abstractmethod
    def outs(self):
        """get workflow outputs"""
        raise NotImplementedError

    # TODO
    def decorate_module(self, mod):
        """"""
        cls = self.__class__
        if not hasattr(cls, '_modules'):
            setattr(cls, '_modules', {})
        
        runnable_name = 'run'
        try:
            mod, runnable_name =  mod.split(':')
        except:
            pass
        
        if runnable_name in self._modules:
            return 
        mod = import_module(mod)
        runnable = getattr(mod, runnable_name)
        
        def wapper(*args, **kwargs):
            new_args = []
            new_kwargs = {}

            # 解析命令行中需要的参数
            need_args, need_kwargs = inspect_args(runnable)

            # 对传入的参数做智能替换, 从配置文件中替换
            for val in args[:len(need_args)]:
                if val in self.config:
                    new_args.append(self.config[val])
                else:
                    new_args.append(val)
            for key, val in kwargs.items():
                if key in need_kwargs:
                    if isinstance(val, str) and val in self.config:
                        new_kwargs[key] = self.config[val]
                    else:
                        new_kwargs[key] = val
            
            # 对传入的特殊的{args}参数进行特殊处理， 因为里面包含task的参数，如resource， path等
            task_args = {}
            if 'args' in new_kwargs and isinstance(new_kwargs['args'], dict): 
                all_args = copy.deepcopy(new_kwargs['args'])
                for field in ['outdir', 'parents', 'resource', 'hooks', 'priority', 'retries', 'expires', 'notes']: # task中可指定的参数
                    if field in all_args:
                        task_args[field] = all_args.pop(field)
                new_kwargs['args'] = all_args
            
                # 命令行参数在{args}里
                for arg in need_kwargs:
                    if arg not in new_kwargs:
                        if arg in new_kwargs['args']:
                            new_kwargs[arg] = new_kwargs['args'].pop(arg)

                # 将{args}变成字符串
                cmd_args = ''
                for key, val in new_kwargs['args'].items():
                    cmd_args += f" {key} "
                    if val is None:
                        cmd_args += ''
                    elif isinstance(val, list):
                        cmd_args += f" {key} ".join([str(i) for i in val])
                    else:
                        cmd_args += str(val)
                new_kwargs['args'] = cmd_args
            
            # 命令行参数必须有值
            for arg in need_kwargs:
                if arg not in new_kwargs:
                    if arg in self.config:
                        new_kwargs[arg] = self.config[arg]
                    else:
                        #raise WorkflowError(f"未指定命令模块参数{arg}")
                        new_kwargs[arg] = ''
           
            # 解决依赖
            if 'parents' not in task_args:
                task_args['parents'] = []
            if self.p is not None:
                task_args['parents'].append(self.p.id)
            
            # 命令行参数在依赖里, 覆盖之前的
            for task_name in self._deps:
                if self._deps[task_name].id in task_args['parents']:
                    for i in range(len(need_args)):
                        if args[i] in self._deps[task_name].outs:
                            new_args[i] = self._deps[task_name].outs[args[i]]
                    for arg in need_kwargs:
                        if arg in self._deps[task_name].outs:
                            new_kwargs[arg] = self._deps[task_name].outs[arg]

            # 生成命令行和输出
            # print(new_kwargs)
            cmdlist, outs = runnable(*new_args, **new_kwargs)
            print(cmdlist)
            # 提交到Task列表
            task_args['analysis'] = self.analysis
            if isinstance(cmdlist, str) or must_cmdstr(cmdlist):
                task_args['shell'] = True

            if 'outdir' not in task_args:
                if self.p is not None:
                    task_args['outdir'] = self.p.outdir
                else:
                    task_args['outdir'] = 'tmpdir'

            task = Task.create(cmdlist=cmdlist, outs=outs, **task_args)
            
            # outs变为绝对路径
            new_outs = {}
            for key, val in task.outs.items():
                if os.path.isabs(val):
                    new_outs[key] = val
                else:
                    new_outs[key] = os.path.abspath(os.path.join(task_args['outdir'], val))
            task.outs = Dict(new_outs)
            # task.save() # 保存到数据库
            if 'task_name' in kwargs:
                task_name = kwargs['task_name']
            elif runnable_name not in self._deps:
                task_name = runnable_name
            else:
                used_names = [ name for name in self._deps.keys() if name.startswith(runnable_name+'#')]
                if len(used_names) == 0:
                    task_name = runnable_name + '#1'
                else:
                    idx = max([ int(name.replace(runnable_name+'#', '')) for name in used_names]) + 1
                    task_name = runnable_name + '#' + str(idx)

            self._deps[task_name] = task

            # 命令输出为下一步输入准备
            self.p = task

            return self

        self._modules[runnable_name] = wapper
    
    def begin(self):
        pass

    def end(self):
        pass

    def getdep(self, task_name):
        if task_name in self._deps:
            return self._deps[task_name]
        else:
            raise WorkflowError("依赖任务还不存在")

    def scatter(self, data, **kwargs):
        inmaps = {}
        for key, val in kwargs.items():
            if val == 'key':
                inmaps['key'] = key
            elif val == 'val':                    # value is str
                inmaps['val'] = key
            elif val[:4] == 'val.':
                try:
                    inmaps[int(val[4:])] = key    # value is list
                except:
                    inmaps[val[4:]] = key         # value is dict
            else:
                pass

        scatter_data = []
        if isinstance(data, dict):
            for key, val in data.items():
                outmaps = {}
                tmpmaps = inmaps.copy()
                outmaps[tmpmaps['key']] = key
                del tmpmaps['key']
                if isinstance(val, (dict, list)):
                    for i in tmpmaps:
                        outmaps[inmaps[i]] = val[i]
                else:
                    outmaps[tmpmaps['val']] = val
                scatter_data.append(outmaps)
        elif isinstance(data, list):
            for val in data:
                outmaps = {}
                if isinstance(val, (dict,list)):
                    for i in inmaps:
                        outmaps[inmaps[i]] = val[i]
                else:
                    outmaps[inmaps['val']] = val
                scatter_data.append(outmaps)
        
        self._scatter = True
        self._scatter_data = scatter_data
        return self


def update_dict(d, u):
    """Recursively updates nested dict d from nested dict u"""
    for key, val in u.items():
        if isinstance(val, collections.abc.Mapping):
            d[key] = update_dict(d.get(key, {}), val)
        else:
            d[key] = u[key]
    return d

def melt_dset(data, **kwargs):
    inmaps = {}
    for key, val in kwargs.items():
        if val == 'key':
            inmaps['key'] = key
        elif val == 'val':                    # value is str
            inmaps['val'] = key
        elif val[:4] == 'val.':
            try:
                inmaps[int(val[4:])] = key    # value is list
            except:
                inmaps[val[4:]] = key         # value is dict
        else:
            pass                              # other is error
    
    scatter_data = []
    if isinstance(data, dict):
        for key, val in data.items():
            outmaps = {}
            tmpmaps = inmaps.copy()
            outmaps[tmpmaps['key']] = key
            del tmpmaps['key']
            if isinstance(val, (dict, list)):
                for i in tmpmaps:
                    outmaps[inmaps[i]] = val[i]
            else:
                outmaps[tmpmaps['val']] = val
            scatter_data.append(outmaps)
    elif isinstance(data, list):
        for val in data:
            outmaps = {}
            if isinstance(val, (dict,list)):
                for i in inmaps:
                    outmaps[inmaps[i]] = val[i]
            else:
                outmaps[inmaps['val']] = val
            scatter_data.append(outmaps)

    return scatter_data

def must_cmdstr(cmdlist):
    """必须使用shell执行"""
    return False

def inspect_args(cab):
    """可调用对象所需参数"""
    need_args = []
    need_kwargs = []
    if isinstance(cab, Cmdline):
        # 解析命令行中需要的参数
        cmdline = cab.cmdline
        for literal_text, field_name, format_spec, conversion in cab.parse_cmdline():
            if field_name:     # 可能为None
                if field_name.isnumeric():
                    need_args.append(field_name)
                else:
                    need_kwargs.append(field_name)
    else:                   # 否则就是定义的函数了
        sig = signature(cab)
        for name, param in sig.parameters.items():
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                if param.default == param.empty:
                    need_args.append(name)
                else:
                    need_kwargs.append(name)

    return need_args, need_kwargs

def substitute_args(need_args, need_kwargs, src, append=True):
    """使用src中的信息替换args"""
    pass
    