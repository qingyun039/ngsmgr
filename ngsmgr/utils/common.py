import collections.abc
from importlib import import_module

def update_dict(d, u):
    """Recursively updates nested dict d from nested dict u"""
    for key, val in u.items():
        if isinstance(val, collections.abc.Mapping):
            d[key] = update_dict(d.get(key, {}), val)
        else:
            d[key] = u[key]
    return d

def dynamic_load(obj_path):
    '''dynamic import attribute, class, func'''
    obj_name = ''
    if ':' in obj_path:
        mod_name, obj_name = obj_path.split(':', 1)

    mod = import_module(mod_name)

    if obj_name:
        obj = getattr(mod, obj_name)
    else:
        obj = mod

    return obj

def flatten_args(args):
    """将字典表示的args转换成用于命令行的字符串args"""
    cmd_args = ''
    for key, val in args.items():
        cmd_args += f" {key} "
        if val is None:
            cmd_args += ''
        elif isinstance(val, list):
            cmd_args += f" {key} ".join([str(i) for i in val])
        else:
            cmd_args += str(val)
    return cmd_args