import socket
import json
import time
import numpy as np

# 创建UDP套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("localhost", 9798))

while True:
    # 发送数据
    # Pcur = [[82863,90452,3000], [84972,90727,3000]]
    # p_search = [[85407,90794,3000], [12699,91338,3000], [63236,9755,3000]]
    # N = max(len(Pcur), len(p_search))
    # ViewR = [4000 for i in range(N)]

    Pcur = [[1,2,0], [3,4,0], [5,6,0], [7,8,0], [8,7,0], [6,5,0], [4,3,0], [2,1,0]]
    p_search = [[10,20,0], [15,10,0], [20,15,0], [20,30,0], [25,15,0], [20,10,0]]
    N = max(len(Pcur), len(p_search))
    ViewR = [3 for i in range(N)]

    dic = {"Pcur": Pcur, "ViewR": ViewR, "p_search": p_search}
    s = json.dumps(dic)

    sock.sendto(s.encode(), ("localhost", 9797))

    # 接收结果
    data, addr = sock.recvfrom(1024)
    res = json.loads(data.decode())
    # print(res["p_next"])

    time.sleep(1)
