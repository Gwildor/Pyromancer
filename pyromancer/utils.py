import importlib
import inspect


def find_functions(packages, into, submodule, ignored=None,
                   when=lambda f: True, ret=lambda f: f):
    for package in packages:
        if isinstance(package, tuple):
            package_settings = package[1]
            package = package[0]
        else:
            package_settings = {}

        if ignored is None:
            ignored = []
        elif not isinstance(ignored, (list, tuple)):
            ignored = package_settings.get(ignored, [])

        ignored = ['{}.{}'.format(package, i) if not i.startswith(package)
                   else i for i in ignored]

        module_name = '{}.{}'.format(package, submodule)
        if module_name in ignored:
            continue

        module = importlib.import_module(module_name)

        modules = [('', module,)]
        modules.extend(inspect.getmembers(module, inspect.ismodule))

        for name, module in modules:
            if module.__name__ in ignored:
                continue

            functions = inspect.getmembers(module, inspect.isfunction)
            into.extend(
                ret(f) for fn, f in functions if
                when(f) and '{}.{}'.format(module.__name__, fn) not in ignored)
