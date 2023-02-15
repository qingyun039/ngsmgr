import collections.abc

def update_dict(d, u):
    """Recursively updates nested dict d from nested dict u"""
    for key, val in u.items():
        if isinstance(val, collections.abc.Mapping):
            d[key] = update_dict(d.get(key, {}), val)
        else:
            d[key] = u[key]
    return d

a = {'a': 1}
b = {'b': 2, 'c': [1,2,3]}

update_dict(a, b)
print(a)
