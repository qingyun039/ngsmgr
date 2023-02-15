class NgsmgrException(Exception):
    '''错误基类'''
    def logerror(self):
        """记录异常"""
        for handle in self.args[1:]:
            if hasattr(handle, 'error') and callable(handle.error):
                handle.error(self.args[0])

class PipelineError(NgsmgrException):
    '''流程相关错误'''
    pass

class NgsmgrConfigError(NgsmgrException):
    '''配置文件相关错误'''
    pass

class AnalysisConfigError(NgsmgrException):
    '''分析配置文件错误'''
    pass

class WorkflowError(NgsmgrException):
    '''流程编写的错误'''
    pass