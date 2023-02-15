import os
import yaml
import string

class CmdFomatter(string.Formatter):
    """实现默认值, 如shell里面的${parameter:-word}"""
    def format_field(self, value, format_spec):
        if format_spec:
            if format_spec[0] == '~' or format_spec[0] == '=':
                if value:
                    return str(value) 
                else:
                    return format_spec[1:]
            elif format_spec[0] == '+':
                if value:
                    return format_spec[1:] + str(value)
            elif format_spec[0] == '-':
                dep = format_spec[1:]
                if self.kwargs.get(dep, ''):
                    return str(value)
                else:
                    return ''

        format_spec = ''
        return string.Formatter.format_field(self, value, format_spec)

    def vformat(self, format_string, args, kwargs):
        self.format_string = format_string
        self.args = args
        self.kwargs = kwargs
        #print(format_string, args, kwargs)
        return string.Formatter.vformat(self, format_string, args, kwargs)

class Cmdline():
    """命令模块类
    使用模板来构建命令模块，实例为可调用对象，返回命令行和命令输出字典。
    模板包括命令行模板cmdlist和输出模板outs，参数必须是字符串。
    {#}形式的参数为必须参数;
    {s}形式的参数为可选参数，没有指定为空字符''
        {s:~default}或{s:=default}设置默认值，当s为False时使用默认值
        {s:+str}表示如果s为True，则用str+s作为值
    """
    def __init__(self, name, cmdline='', outs=None, defaults=None, **kwargs):
        self.name = name
        self.cmdline = cmdline
        self.outs = outs
        self.defaults = defaults

        self._formatter = CmdFomatter()
    
    def __call__(self, *args, **kwargs):
        new_cmdline = self._formatter.format(self.cmdline, *args, **kwargs)
        new_outs = {}
        for key, val in self.outs.items():
            nkey = self._formatter.format(key, **kwargs)
            nval = self._formatter.format(val, **kwargs)
            new_outs[nkey] = nval
        return new_cmdline, new_outs

    def parse_cmdline(self):
        return self._formatter.parse(self.cmdline)


MODDIR = os.path.dirname(__file__)

cmdtpl_fn = 'common_utils.yml'
cmdtpl_fn = os.path.join(MODDIR, cmdtpl_fn)
with open(cmdtpl_fn) as f:
    cmdtpls = yaml.safe_load(f)
    for key, val in cmdtpls.items():
        globals()[key] = Cmdline(key, **val)


# argv = dict(
#     path = '/path/to/fastp',
#     sample = 'sample',
#     args = []
# )
# cmdlist, outs = fastp('read1', 'read2', 'fd', path='/path/to/fastp', sample='sample', args='args')
# #cmdlist, outs = bwa_mem('read1', 'read2', 'fd', path='/path/to/fastp', sample='sample', args='args')
# #print(globals())
# print(cmdlist, outs)