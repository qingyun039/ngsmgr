"""通常是那些根据输入不同会有不同的输出文件的命令"""
import re
import inspect
import functools

def cmdline(path='', prefix='', args=''):
    def decorator(func):
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            funcode = inspect.getsourcelines(func)
            new_funcode = []
            def_began = False
            for code in funcode[0]:
                if re.match(r'\s*def', code):
                    def_began = True
                    match = re.search(r'\*\*\w+', code)
                    if match:
                        idx = match.start(0)
                        post_code = code[idx:]
                        code = code[:idx]
                        if 'path' not in sig.parameters.keys():
                            code += f"path={path},"
                        if 'prefix' not in sig.parameters.keys():
                            code += f"prefix={prefix},"
                        if 'args' not in sig.parameters.keys():
                            code += f"args={args},"
                        code += post_code
                    else:
                        idx = code.index(')')
                        post_code = code[idx:]
                        code = code[:idx]
                        if 'path' not in sig.parameters.keys():
                            code += f",path={path}"
                        if 'prefix' not in sig.parameters.keys():
                            code += f",prefix={prefix}"
                        if 'args' not in sig.parameters.keys():
                            code += f",args={args}"
                        code += post_code
                if def_began:
                    new_funcode.append(code)

            new_funcode = ''.join(new_funcode)
            exec(new_funcode)
            new_func = locals()[func.__name__]

            # if 'path' not in kwargs:
            #     kwargs['path'] = path
            # if 'prefix' not in kwargs:
            #     kwargs['prefix'] = prefix
            cmdline, outs = new_func(*args, **kwargs)
            return cmdline, outs
        
        return wrapper
    return decorator

def mosdepth(bamfile, path='', prefix='', args=''):
    """mosdepth"""
    path = path or 'mosdepth'
    prefix = prefix or 'test'

    cmdline = f"{path} {args} {prefix} {bamfile}"

    outs = {
        'summary': f"{prefix}.mosdepth.summary.txt",
        'global_dist': f"f{prefix}.mosdepth.global.dist.txt",
    }
    if '-b' in args or '--by' in args:
        outs['region_dist'] = f'{prefix}.mosdepth.region.dist.txt'
        outs['regions'] = f'{prefix}.regions.bed.gz'
    if '-q' in args or '--quantize' in args:
        outs['quantized'] = f'{prefix}.quantized.bed.gz'
    if '-T' in args or '--thresholds' in args:
        outs['thresholds'] = f'{prefix}.thresholds.bed.gz'
    if '-n' not in args and '--no-per-base' not in args:
        if '--d4' in args:
            outs['perbase'] = f'{prefix}.per-base.bed.gz'
        else:
            outs['perbase'] = f'{prefix}.per-base.d4'
    
    return cmdline, outs

@cmdline(path='gatk', prefix='sample')
def gatk_splitintervals(reference, interval, scatter):
    cmdline = f"{path} -R {reference} -scatter {scatter} -O . -L {interval} {args}"
    outs = { f"interval_{i}": f"{i:04d}-scattered.interval_list"for i in range(int(scatter)) }
    return cmdline, outs