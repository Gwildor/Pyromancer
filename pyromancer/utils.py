import datetime
import importlib
import inspect
from types import GeneratorType


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

        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue

        modules = [('', module,)]
        modules.extend(inspect.getmembers(module, inspect.ismodule))

        for name, module in modules:
            if module.__name__ in ignored:
                continue

            functions = inspect.getmembers(module, inspect.isfunction)
            into.extend(
                ret(f) for fn, f in functions if
                when(f) and '{}.{}'.format(module.__name__, fn) not in ignored)


def process_messages(result, with_target=False):
    from pyromancer.objects import Timer

    if isinstance(result, (list, GeneratorType)):
        messages = result
    else:
        messages = [result]

    for msg in messages:
        get_target = with_target

        if isinstance(msg, tuple):
            timer = False
            if isinstance(msg[0], (datetime.datetime, datetime.timedelta)):
                scheduled = msg[0]
                msg = msg[1:]
                timer = True

                if callable(msg[0]):
                    get_target = False
                    target = None
                else:
                    get_target = True

            if get_target:
                target = msg[0]
                msg = msg[1:]

            last = len(msg) - 1
            msg, args, kwargs = msg[0], list(msg[1:last]), msg[last]

            # If the result is (msg, positional argument,), make sure it
            # still works correctly as expected for the formatting.
            if not isinstance(kwargs, dict):
                if last > 0:
                    args.append(kwargs)

                kwargs = {}

            if timer:
                yield Timer(scheduled, msg, *args, target=target, **kwargs)
                continue
        elif isinstance(msg, Timer):
            yield msg
            continue
        else:
            target, args, kwargs = None, [], {}

        if get_target:
            yield target, msg, args, kwargs
        else:
            yield msg, args, kwargs
