import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

fontsize = 16
data = [[80, 70, 80, 90, 90, 80, 80, 80, 100, 80],
        [85, 80, 90, 85, 85, 80, 95, 95, 80, 80],
        [90, 83.33, 86.66, 90, 96.66, 86.66, 93.33, 90, 100, 93.33],
        [92.5, 87.5, 90, 92, 93, 87.5, 97.5, 92.5, 95, 92],
        [88, 88, 86, 88, 90, 92, 96, 92, 84, 92]]
labels = [10, 20, 30, 40, 50]
ax2x = [1, 2, 3, 4, 5]
ratios = [1101/1344*100, 2524/3055*100, 3928/4455*100, 5042/5464*100, 5924/6910*100]
ave = [np.average(a) for a in data]
# print(ave)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.boxplot(data, labels=labels, showmeans=True, patch_artist=True)
ax.grid(linestyle="--", alpha=0.3)
ax.set_xlabel("The number of WLs", size=fontsize)
ax.set_ylabel("Coverage rate (%)", size=fontsize)
ax.set_ylim(78, 102)
ax.tick_params(axis='both', which='major', labelsize=fontsize)

ax2 = ax.twinx()
ax2.plot(ax2x, ratios, color="c", linewidth=3)
ax2.set_ylabel("Average return ratio (%)", size=fontsize)
ax2.set_ylim(78, 102)
ax2.tick_params(axis='both', which='major', labelsize=fontsize)
# ax2.axes.yaxis.set_visible(False)       # hide y axis, open when plot average

plt.tight_layout()
plt.savefig("31.png", dpi=1200)
plt.show()
