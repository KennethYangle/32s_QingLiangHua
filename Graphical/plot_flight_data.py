import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d


def plot_data(ax, data, save_name="111"):
    allocation = data["allocation"]
    for p in allocation:
        ax.plot([data["drones"][p[0]][0], data["circles"][p[1]][0]], 
                [data["drones"][p[0]][1], data["circles"][p[1]][1]], 
                [data["drones"][p[0]][2], data["circles"][p[1]][2]])
    for d in data["drones"].values():
        ax.scatter(d[0], d[1], d[2], marker="o")
    for c in data["circles"].values():
        ax.scatter(c[0], c[1], c[2], marker="*", color="r")
    
    ax.set_ylabel('Y')
    ax.set_xlabel('X')
    ax.set_zlabel('Z')
    ax.view_init(elev=25, azim=-2.5)
    # ax.set_ylim(-50, 100)
    # ax.grid(False)
    ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    fig.savefig("{}.png".format(save_name), dpi=600)


flight_data_file = open("flight_data.json")
flight_data = json.load(flight_data_file)

fig = plt.figure(1)
ax1 = plt.axes(projection='3d')
plot_data(ax1, flight_data["5v5move"]["checkpoint1"], "5v5move_checkpoint1")
fig = plt.figure(2)
ax2 = plt.axes(projection='3d')
plot_data(ax2, flight_data["5v5move"]["checkpoint2"], "5v5move_checkpoint2")

fig = plt.figure(3)
ax3 = plt.axes(projection='3d')
plot_data(ax3, flight_data["5v4to5"]["checkpoint1"], "5v4to5_checkpoint1")
fig = plt.figure(4)
ax4 = plt.axes(projection='3d')
plot_data(ax4, flight_data["5v4to5"]["checkpoint2"], "5v4to5_checkpoint2")

fig = plt.figure(5)
ax5 = plt.axes(projection='3d')
plot_data(ax5, flight_data["5v5to4"]["checkpoint1"], "5v5to4_checkpoint1")
fig = plt.figure(6)
ax6 = plt.axes(projection='3d')
plot_data(ax6, flight_data["5v5to4"]["checkpoint2"], "5v5to4_checkpoint2")
plt.show()
