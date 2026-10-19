# -*- coding: utf-8 -*-

from _weakref import proxy
from _weakref import ref


class CallbackSavedArgs(object):
    def __init__(self, cls, obj, func, args):
        object.__init__(self)
        self.cls = cls
        self.objRef = ref(obj)
        self.func = proxy(func)
        self.args = args

    def __call__(self, *args):
        if self.objRef:
            return self.func(self.objRef(), *self.args)

    def __nonzero__(self):
        return bool(self.objRef)


class CallbackNoArgs(object):
    def __init__(self, cls, obj, func):
        object.__init__(self)
        self.cls = cls
        self.objRef = ref(obj)
        self.func = proxy(func)

    def __call__(self, *args):
        if self.objRef:
            return self.func(self.objRef())

    def __nonzero__(self):
        return bool(self.objRef)


class Callback(object):
    def __init__(self, cls, obj, func):
        object.__init__(self)
        self.cls = cls
        self.objRef = ref(obj)
        self.func = proxy(func)

    def __call__(self, *args):
        if self.objRef:
            return self.func(self.objRef(), *args)

    def __nonzero__(self):
        return bool(self.objRef)


def MakeCallback(func):
    try:
        if func.im_func.func_code.co_argcount > 1:
            return Callback(func.im_class, func.im_self, func.im_func)
        else:
            return CallbackNoArgs(func.im_class, func.im_self, func.im_func)
    except AttributeError:
        # Handle special function/method types:
        #   AttributeError: 'builtin_function_or_method' object has no attribute 'im_func'
        #   AttributeError: 'cython_function_or_method' object has no attribute 'im_func'
        return func


class Event(object):
    def __init__(self, func, *args):
        object.__init__(self)
        self.callback = MakeCallback(func)
        self.args = args

    def __call__(self, *args):
        if args:
            args = self.args + args
            return self.callback(*args)
        else:
            return self.callback(*self.args)

    def __nonzero__(self):
        return bool(self.callback)


def MakeEvent(event):
    # Ignore None, 0, etc. that might get passed to this function
    if not event:
        return None

    if isinstance(event, Event):
        return event
    else:
        return MakeCallback(event)
