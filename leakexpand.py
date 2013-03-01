import os
import sys
from collections import defaultdict
import yaml
import jinja2

spec, = sys.argv[1:]

leakname = os.path.splitext(os.path.basename(spec))[0]

class Hook(object):
    def __init__(self):
        self.probes = {}

    @property
    def func(self):
        return '{}$${}'.format(self.cls, self.method.replace(':', '$_'))

hooks = defaultdict(Hook)

with open(spec, 'r') as f:
    probes = yaml.load(f.read())

for probe, pattrs in probes.items():
    probeargs = pattrs['args']
    for cls, methods in pattrs['methods'].items():
        for method in methods:
            name = method['name']
            assert name[:1] == '-', "only instance methods are supported yet"
            sel = name[1:]
            rtype = method['rtype']

            hook = hooks[(cls, sel)]
            hook.cls = cls
            hook.method = sel # TODO: automatic type discovery
            hook.rtype = rtype
            hook.args = method['args']

            hook.probes['{}_{}'.format(leakname, probe.replace('__', '_')).upper()] = probeargs

def expand(template, output, **kwargs):
    with open(template, 'r') as t:
        text = jinja2.Template(t.read()).render(**kwargs)
        with open(output, 'w+') as o:
            o.write(text)

path_prefix = 'leaks/{}'.format(leakname)
os.makedirs(path_prefix)
path = lambda suffix: '{}/{}.{}'.format(path_prefix, leakname, suffix)

expand('hook.template', path('m'),
        leakname=leakname, hooks=hooks.values())
expand('provider.template', path('provider.d'),
        leakname=leakname, probes=[(name, attrs['args']) for name, attrs in probes.items()])
expand('makefile.template', path_prefix + '/Makefile',
        leakname=leakname)
expand('lldb.template', path('lldb'),
        leakname=leakname)
