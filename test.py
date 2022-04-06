import ret_tools as rt

def function_failed(arg1, arg2):
    print("Failed: {}, {}".format(arg1, arg2)) # Failed: func failed
    
@rt.def_ret(function_failed, "func", "failed")
def func():
    raise Exception("Failed")
    
def main():
    ret = func()
    print(ret.success) # True
    print(ret.msg) # Exception("Failed")
    
if __name__ == "__main__":
    main()
