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
    # algs.Hungarian(TL, WL)
    algs.SolveGG(TL, WL)

    p_next = [0 for i in range(N)]
    for r in algs.tree_result:
        p_next[r[0].parent_id] = HS.drones[r[1].parent_id].id
    return np.array(p_next)


if __name__ == "__main__":
    Pcur = np.array([[82863,90452,3000], [84972,90727,3000]])
    p_search = np.array([[85407,90794,3000], [12699,91338,3000], [63236,9755,3000]])
    N = max(np.size(Pcur, 0), np.size(p_search, 0))
    ViewR = np.array([4000 for i in range(N)])
    p_next = useGTA(Pcur, ViewR, p_search)
    # print(p_next)

    Pcur = np.array([[1,2,0], [3,4,0], [5,6,0], [7,8,0], [8,7,0], [6,5,0], [4,3,0], [2,1,0]])
    p_search = np.array([[10,20,0], [15,10,0], [20,15,0], [20,30,0], [25,15,0], [20,10,0]])
    N = max(np.size(Pcur, 0), np.size(p_search, 0))
    ViewR = np.array([3 for i in range(N)])
    p_next = useGTA(Pcur, ViewR, p_search)
    # print(p_next)

    Pcur = np.array([[1,2,0], [3,4,0], [5,6,0], [7,8,0], [8,7,0], [6,5,0], [4,3,0], [2,1,0]])
    p_search = np.array([[10,20,0], [15,10,0], [20,15,0], [20,30,0], [25,15,0], [20,10,0]])
    N = max(np.size(Pcur, 0), np.size(p_search, 0))
    ViewR = np.array([3 for i in range(N)])
    p_next = useGTA(Pcur, ViewR, p_search)
    # print(p_next)
