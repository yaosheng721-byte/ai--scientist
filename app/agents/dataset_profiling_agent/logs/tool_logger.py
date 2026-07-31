import datetime



def tool_log(tool_name,status):


    time = datetime.datetime.now()


    print(
        f"[{time}] [{tool_name}] {status}"
    )