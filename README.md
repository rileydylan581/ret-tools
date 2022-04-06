# ret-tools

ret-tools is a small library used for formating function responses, handling function exceptions, executing and handling asynchronous tasks. View examples below:

## Handling Functions

ret-tools is built off two main functions: `run()` and `run_async()`

both return a RetResp with four properties: 

success (bool True or False),
msg ("Success" or Exception),
tb (None or Exception Traceback),
resp (None or response of original function)

RetResp can be treated as 

a list `[success, msg, tb, resp]`,
a dict `{"success": True, "msg": "Success", "tb": None, "resp": "some random data"}`,
or a str: `Succeeded: some random data`,

Example of `run()`:
```python3
import ret_tools as rt

def func(name):
    return "Hi {}".format(name)


def main():
    ret = rt.run(func, ("John Smith"))
    
    print(ret.success)
    # True
    
    print(ret.msg)
    # Success
    
    print(ret.resp)
    # "Hi John Smith"

    print(tuple(ret))
    # (True, "Success", None, "Hi John Smith")

if __name__ == "__main__":
    main()
```

Example of `run_async()`
```python3
import ret_tools as rt
import asyncio

async def afunc(name):
    await asyncio.sleep(1)
    return "HI {}".format(name)

def main():
    ret = asyncio.run(rt.run_async(afunc("John Smith")))
    
    print(ret.success)
    # True
    
    print(ret.msg)
    # Success
    
    print(ret.resp)
    # "Hi John Smith"

    print(tuple(ret))
    # (True, "Success", None, "Hi John Smith")

if __name__ == "__main__":
    main()

```

If a function throws an Exception the response is as follows:
```python3
import ret_tools as rt

def func():
    raise Exception("Something went wrong")


def main():
    ret = rt.run(func)
    
    print(ret.success)
    # False
    
    print(ret.msg)
    # Exception("Something went wrong")
    
    print(ret.resp)
    # None

    print(tuple(ret))
    # (False, Exception("Something went wrong"), "Traceback: ...", None)

if __name__ == "__main__":
    main()
```

ret-tools can be configured with a RetConfig object, you can specify a failed callback, error callback, and a task callback

failed callback `ret_config.ff` gets called when a function throws an error, this can change on a function to function basis, you can also specify custom arguments, an example would be a websocket client that closes the connection when a send or recv fails

error callback `ret_config.ec` gets called every time a function throws an error, it is global and can't change on a function-to-function basis, this can be used for logging purposes, the argument will be a RetResp

task callback `ret_config.tc` gets called when a async task finishes, this can be changed on a task to task basis, the argument will be a RetResp

Example:
```python3
import ret_tools as rt

def error_callback(err_resp):
    print(err_resp) # Failed: Exception Text

ret_config = rt.RetConfig(ec=error_callback)
rt.init(ret_config)

def failed(function_name, other_arg):
    print("{} Failed, {}".format(function_name, other_arg))
    # Do something if function fails
    
def func(*args):
    raise Exception("Function Failed")
    
def main():
    #            function, fargs, failed_func, *failed_args
    ret = rt.run(func,     (),    failed,      "Name of function", "some other argument")
    
    print(ret.success) # False
    
if __name__ == "__main__":
    main()
```

## Function Decorators

ret-tools offer two different function decorators: `@def_ret()` and `@async_ret()`
each decorator will pass the function through `rt.run()` or `rt.run_async()`

Example:
```python3
import ret_tools as rt

@rt.def_ret()
def func():
    return "some random data"
    
def main():
    ret = func()
    print(ret.success) # True
    print(ret.resp) # "some random data"
    print(tuple(ret)) # (True, "Success", None, "some random data")
    
if __name__ == "__main__":
    main()
```

You can also specify custom failed callbacks through the decorators

Example:
```python3
import ret_tools as rt

def function_failed(arg1, arg2):
    print("Failed: {} {}".format(arg1, arg2)) # Failed: func failed
    
@rt.def_ret(function_failed, "func", "failed")
def func():
    raise Exception("Failed")
    
def main():
    ret = func()
    print(ret.success) # True
    print(ret.msg) # Failed
    
if __name__ == "__main__":
    main()
```

## Handling Tasks

ret-tools can also be used to handle asynchronous tasks, there are two main methods: `create_task()`, `wait_task()`

Example of `create_task()`:
```python3
import ret_tools as rt
import asyncio

def task_callback(resp): # response is a RetResp object
    print(resp) # Succeeded: Hi John Smith

async def task(name):
    await asyncio.sleep(1)
    return "Hi {}".format(name)
    
def main():
    t = rt.create_task(task("John Smith"), task_callback) # returns asyncio.Task
    
if __name__ == "__main__":
    main()
```

`create_task()` works even when no asyncio event loop is present, ret-tools will detect if a loop is running, if not it will create a new loop and run it in a seperate thread then it will execute the task from there

Example of `wait_task()`:
```python3
import ret_tools as rt
import asyncio
    
async def task(name):
    await asyncio.sleep(1)
    return "Hi {}".format(name)
    
def main():
    resp = rt.wait_task(task("John Smith"))
    
    print(resp) # Succeeded: Hi John Smith
    
async def async_main():
    resp = await rt.run_async(task("John Smith"))
    print(resp) # Succeeded: Hi John Smith
    
    resp = await rt.create_task(task("John Smith"))
    print(resp) # Succeeded: Hi John Smith
    
if __name__ == "__main__":
    main()
    asyncio.run(async_main())
```
`rt.wait_task()` is equivilent to `await rt.create_task()` which is equivilent to `await rt.run_async()`

If there is no event loop use `rt.wait_task()`, If you have an event loop and you want the response imediately use `await rt.run_async()`, if you want the response in a callback use `rt.create_task(task(), callback)`

## Good and Bad

RetResp's are built off two functions `good()` and `bad()`

`good()` returns `(True, "Success", None)` always

`bad()` returns `(False, Exception, Traceback)` using `sys.exc_info()` and `traceback.print_exc()`

Example:
```python3
import ret_tools as rt

def main():
    ret = None
    try:
        print("Do Something Here")
        ret = rt.good()
    except:
        ret = rt.bad()
    print(tuple(ret)) # (True, "Success", None)
    
    ret = None
    try:
        raise Exception("Something went wrong")
        ret = rt.good() # Won't happen because exception is raised
    except:
        ret = rt.bad()
    print(tuple(ret)) # (False, Exception("Something went wrong"), "Traceback: ...")
    
if __name__ == "__main__":
    main()
```
