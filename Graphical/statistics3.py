import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

fontsize = 16
data = [[88, 88, 86, 88, 90, 92, 96, 92, 84, 92],
        [92, 98, 96, 98, 98, 92, 92, 92, 88, 100],
        [100, 96, 98, 98, 96, 100, 100, 100, 100, 98],
        [100, 100, 100, 98, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 98, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 98, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
        [100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
         100, 100, 100, 100, 100, 100, 100, 100, 100, 100]]
labels = [1, 2, 3, 4, 5]
ax2x = [1, 2, 3, 4, 5]
ave = [np.average(a) for a in data]
# print(ave)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.boxplot(data, labels=labels, showmeans=True, patch_artist=True)
ax.grid(linestyle="--", alpha=0.3)
ax.set_xlabel("Reallocation times", size=fontsize)
ax.set_ylabel("Coverage rate (%)", size=fontsize)
ax.set_ylim(78, 102)
ax.tick_params(axis='both', which='major', labelsize=fontsize)

ax2 = ax.twinx()
ax2.plot(ax2x, ave, color="c", linewidth=3)
ax2.set_ylim(78, 102)
ax2.axes.yaxis.set_visible(False)       # hide y axis, open when plot average
ax2.tick_params(axis='both', which='major', labelsize=fontsize)

plt.tight_layout()
plt.savefig("33.png", dpi=1200)
plt.show()
