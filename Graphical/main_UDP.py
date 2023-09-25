import numpy as np
random_seed = 367528110
if random_seed < 0:
    random_seed = np.random.randint(1<<32-1)
np.random.seed(random_seed)
# print("random_seed: {}".format(random_seed))

from swarms import Drone, Swarm, Unit, List
from algorithm import Algorithm

import sys
from logger import Logger
sys.stdout = Logger()

import socket
import struct
import time
import json

def useGTA(Pcur, ViewR, p_search):
    N = np.size(Pcur, 0)
    IS = Swarm(N, camp="Interceptor", swarm_pos=Pcur, R=ViewR)
    m = np.size(p_search, 0)
    HS = Swarm(m, camp="Hostile", swarm_pos=p_search, R=ViewR)
    # print(IS)
    # print(HS)
    algs = Algorithm()
    TL, WL = algs.ConstructList(HS, IS)
    # print(TL)
    # print(WL)
    G = WL.ConstructGraph()
    # print(G)
    algs.GetNeighborhood(TL, WL)
    algs.CalcPayoff(TL, WL, M=500)
    algs.Hungarian(TL, WL)
    p_next = [0 for i in range(N)]
    for r in algs.hungarian_result:
        # print(r[1].id, r[0].id)
        p_next[r[1].id] = TL.units[r[0].id].parent_id
    return np.array(p_next)


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 9797))

    while True:
        # 接收数据
        data, addr = sock.recvfrom(8192)
        data_raw = struct.unpack("450d", data)
        data_np = np.reshape(data_raw, (150,3))
        data_Pcur = data_np[:100,:]
        data_p_search = data_np[100:,:]
        
        N, m = 0, 0
        for i in range(100):
            if not np.any(data_Pcur[i]):
                break
            N += 1
        Pcur = data_Pcur[:N,:]
        for i in range(50):
            if not np.any(data_p_search[i]):
                break
            m += 1
        p_search = data_p_search[:m,:]
        # print("Pcur:", Pcur)
        # print("p_search", p_search)

        N = max(N, m)
        ViewR = np.array([1000 for i in range(N)])

        # 处理数据
        p_next = useGTA(Pcur, ViewR, p_search)
        # print("p_next:", p_next)

        # 发送结果
        p_next_zeros = np.zeros(100)
        ll = len(p_next)
        p_next_zeros[:ll] = p_next
        data_p_next = p_next_zeros.flatten()
        data_p_next_raw = struct.pack(f"{len(data_p_next)}d", *data_p_next)
        sock.sendto(data_p_next_raw, ("localhost", 9798))
        
        time.sleep(0.1)