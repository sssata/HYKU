import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from curlyBrace import curlyBrace

t = np.linspace(0,30,1000)

pos_real = 3 * t

slow_cost = 15
pos_slow = np.floor(pos_real/slow_cost)*slow_cost

fast_const = 6
pos_fast = np.floor(pos_real/fast_const)*fast_const

fig, ax = plt.subplots()

print(t)
print(pos_real)


ax.plot(t, pos_real, '--')
ax.plot(t, pos_slow)
ax.plot(t, pos_fast)
curlyBrace(fig, ax, [10.4,30], [10.4,24], 0.26, bool_auto=True, str_text="", color='black', lw=2, int_line_num=1)
ax.annotate("up to 6 px of position error at 500 Hz", (11.6,27), va="center")
curlyBrace(fig, ax, [15.4,45], [15.4,30], 0.1, bool_auto=True, str_text="", color='black', lw=2, int_line_num=1)
ax.annotate("up to 15 px of position error\nat 200 Hz", (16.8,37.5), va="center")
ax.set_ylabel("Position (px)")
ax.set_xlabel("Time (ms)")
ax.set_title("Effect of Polling Rate at 3000 px/second movement")
ax.legend(("Actual", "Sensed (200 Hz)", "Sensed (500 Hz)"))

plt.show()