import asyncio
import sys
import traceback
import types
import threading

class File:
    def __init__(self):
        self.str = ""
        self.closed = False
        self._writable = True
        self._readable = True
    def readable(self):
        return self._readable
    def writable(self):
        return self._writable
    def read(self):
        if self.closed or not self._readable:
            raise
        return self.str
    def write(self, data):
        if self.closed or not self._writable:
            raise
        self.str += data
    def close(self):
        self.closed = True
        self._readable = False
        self._writable = False
    def fileno(self):
        raise OSError()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class RetResp:
    def __init__(self, success:bool, msg:str, tb:str, resp:any) -> None:
        self.success = success
        self.msg = msg
        self.tb = tb
        self._resp = resp

    @property
    def resp(self):
        if type(self._resp) == list or type(self._resp) == dict:
            return self._resp.copy()
        return self._resp
    
    def __getitem__(self, i):
        if type(i) == int:
            return [self.success, self.msg, self.tb, self.resp][i]
        elif type(i) == str:
            return eval("self.{}".format(i))
        else:
            return None
  
    def __str__(self):
        if self.success:
            return "Succeeded: {}".format(self.resp)
        return "Failed: {}".format(self.msg if self.msg != "" else "No Msg")

class RetConfig:
    def __init__(self, fc=None, tc=None, ec=None):
        self.fc = fc
        self.tc = tc
        self.ec = ec
    def copy(self):
        return RetConfig(self.fc, self.tc, self.ec)

ret_conf = RetConfig()
def init(_ret:RetConfig) -> None:
    global ret_conf
    ret_conf = _ret

def good() -> tuple:
    return (True, "Success", None)

def bad() -> tuple:
    sf = File()
    traceback.print_exc(file=sf)
    return (False, sys.exc_info()[1], sf.read())

def run(func, fargs=(), *args, **kwargs):
    _resp = None
    _ret = ()
    try:
        _resp = func(*fargs)
        _ret = good()
    except:
        _ret = bad()
        if ret_conf.ec:
            ret_conf.ec(RetResp(*_ret, _resp))
        if len(args) > 0:
            if callable(args[0]):
                args[0](*args[1:])
            else:
                if ret_conf.fc:
                    ret_conf.fc(*args[0])

    return RetResp(*_ret, _resp)

async def run_async(cor, *args, **kwargs):
    _resp = None
    _ret = ()
    try:
        _resp = await cor
        _ret = good()
    except:
        _ret = bad()
        if ret_conf.ec:
            ret_conf.ec(RetResp(*_ret, _resp))
        if len(args) > 0:
            if type(args[0]) == types.CoroutineType:
                await args[0]
            elif callable(args[0]):
                args[0](*args[1:])
            else:
                if ret_conf.fc:
                    ret_conf.fc(*args[0])
    return RetResp(*_ret, _resp)

def def_ret(*args, **kwargs):
    def inner(func):
        def wrapper(*wargs, **wkwargs):
            return run(func, wargs, *args, **kwargs)
        wrapper.ret = True
        return wrapper
    return inner

def async_ret(*args, **kwargs):
    def inner(func):
        async def wrapper(*wargs, **wkwargs):
            return await run_async(func(*wargs, **wkwargs), *args, **kwargs)
        wrapper.ret = True
        return wrapper
    return inner

def ret_task_callback(task) -> None:
    if hasattr(task, "_my_callback"):
        task._my_callback(task.result())
    if hasattr(task, "_extra_callback"):
        task._extra_callback(task.result())
    if task._threadsafe:
        task._loop.call_soon_threadsafe(task._loop.stop)
        

def wait_task(task, callback=None) -> RetResp:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _thread = threading.Thread(target=loop.run_forever)
    _thread.start()
    threadsafe = True

    if not getattr(task, "ret", False):
        task = run_async(task)
    t = None
    t = asyncio.run_coroutine_threadsafe(task, loop)
    t._threadsafe = True
    t._loop = loop
    if callback:
        t._my_callback = callback
    if ret_conf.tc:
        t._extra_callback = ret_conf.tc
    t.add_done_callback(ret_task_callback)

    _thread.join()
    return t.result()
        
    

def create_task(task, callback=None, loop=None) -> asyncio.Task:
    threadsafe = False
    if loop == None:
        try:
            loop = asyncio.get_running_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            threading.Thread(target=loop.run_forever).start()
            threadsafe = True

    if not getattr(task, "ret", False):
        task = run_async(task)
    t = None
    if threadsafe:
        t = asyncio.run_coroutine_threadsafe(task, loop)
        t._threadsafe = True
        t._loop = loop
    else:
        t = loop.create_task(task)
        t._threadsafe = False
    if callback:
        t._my_callback = callback
    if ret_conf.tc:
        t._extra_callback = ret_conf.tc
    t.add_done_callback(ret_task_callback)
    return t
