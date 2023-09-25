import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

fontsize = 16
data = [[92.5, 90, 90, 92.5, 95, 97.5, 95, 92.5, 97.5, 90],
        [92, 88, 96, 88, 88, 92, 92, 92, 98, 92],
        [85, 80, 90, 85, 85, 80, 95, 95, 80, 80],
        [93.75, 100, 100, 93.75, 93.75, 93.75, 100, 87.5, 93.75, 87.5],
        [100, 100, 100, 90, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 90, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 90, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 90, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 100, 100, 100, 100, 100, 100, 100]]
labels = [0.5, 0.8, 1, 1.25, 2]
ax2x = [1, 2, 3, 4, 5]
ave = [np.average(a) for a in data]
# print(ave)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.boxplot(data, labels=labels, showmeans=True, patch_artist=True)
ax.grid(linestyle="--", alpha=0.3)
ax.set_xlabel(r"$\left|{\cal I}\right|/\left|{\cal H}\right|, \left|{\cal I}\right|=20$", size=fontsize)
ax.set_ylabel("Coverage rate (%)", size=fontsize)
ax.set_ylim(78, 102)
ax.tick_params(axis='both', which='major', labelsize=fontsize)

ax2 = ax.twinx()
ax2.plot(ax2x, ave, color="c", linewidth=3)
ax2.set_ylim(78, 102)
ax2.axes.yaxis.set_visible(False)       # hide y axis, open when plot average
ax2.tick_params(axis='both', which='major', labelsize=fontsize)

plt.tight_layout()
plt.savefig("32.png", dpi=1200)
plt.show()
