from importlib import import_module

class Foo:
    modules = []
    def __init__(self):
        self.name = self.__class__.__name__

        for m in self.modules:
            self.decorate_modules(m)
    
    def __getattr__(self, name):
        if name in self._modules:
            return self._modules[name]

        raise AttributeError


    def decorate_modules(self, mod):
        cls = self.__class__
        if not hasattr(cls, '_modules'):
            setattr(cls, '_modules', {})
        func_name = 'run'
        try:
            mod, func_name =  mod.split(':')
        except:
            pass
        if func_name in self._modules:
            return 
        mod = import_module(mod)
        func = getattr(mod, func_name)

        def wrapper(*argc, **kwargv):
            func(*argc, **kwargv)
            print("wrapper...")

        getattr(cls, '_modules')[func_name] = wrapper
        # self._modules[func_name] = wrapper


class Bar(Foo):
    modules = ['__main__:hello']

    def run(self):
        self.hello(self.name)


def hello(name):
    print(f'hello, {name}!')

def main():
    b = Bar()
    print(b._modules)
    b.run()

if __name__ == '__main__':
    main()
