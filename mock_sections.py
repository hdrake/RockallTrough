
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os.path

import xmitgcm as xmit
import xarray as xr

from utils import *

ds = load_all_data()

fig, axes = plt.subplots(1,2, figsize=(13, 7))
ax = axes[0]

ds["Depth"].plot.contour(ax=ax, levels=np.arange(0, 4000, 500), cmap="Greys", alpha=0.3)
release = [-11.895, 54.233]
ax.plot(release[0], release[1], "C3x", markersize=10)

hoverplot = ax.plot([],[])

# Enter username
name = input("Please enter your full name: ")

# Number of samples
N = input("How many casts would you like to make? ")

try:
	N=int(N)
except:
	print("Please enter a positive integer.")
	exit()

if N>0:
	pass
else:
	print("Please enter a strictly positive integer.")
	exit()

ax.set_title(f"You have {N} casts left!", loc="left")
ax.grid(alpha=0.2)
ax.set_title("")
ax.set_ylim(53.5, 57)
ax.set_xlim(-15.2, -10.305)
axes[1].set_title("")

class PatternCanvas:
	def __init__(self, fig):
		self.fig = fig
		self.ax = fig.axes[0]
		self.hoverplot = hoverplot

		self.N = N
		self.name = name

	def connect(self):
		self.cid_button = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
		#self.cid_key = self.fig.canvas.mpl_connect('key_press_event', self.onkey)
		self.cid_close = self.fig.canvas.mpl_connect('close_event', self.onclose)
		self.cid_hover = self.fig.canvas.mpl_connect("motion_notify_event", self.onhover)
	
	# Click event handler: toggle cells
	def onclick(self, event):
		if event.inaxes == self.ax:
			x = event.xdata
			y = event.ydata
			print(f"Cast {self.N}: ({np.round(x,3)}, {np.round(y,3)})")
			self.N -= 1
			
			sax = axes[1]
			sample = ds.isel(time=-1).sel(XC=x, YC=y, method="nearest")
			ax.scatter(
				sample["XC"],
				sample["YC"],
				s = 40,
				c = sample["c_Zint"],
				cmap = plt.get_cmap("Purples"),
				marker = "o",
				edgecolors = "k",
				linewidths = 1.5,
				norm = matplotlib.colors.LogNorm(vmin=3e-12, vmax=3e-9)
			)
			sample["c"].plot(ax=sax, y="Z")
			ax.set_title(f"You have {self.N} casts left!", loc="left")
			plt.pause(0.001)

			if self.N==0:
				self.end()
				plt.pause(0.001)

	def onhover(self, event):
		if event.inaxes == self.ax:
			self.hovering = (event.xdata, event.ydata)
			
			self.hoverplot[0].remove()
			self.hoverplot = ax.plot(
				self.hovering[0],
				self.hovering[1],
				markersize=14,
				marker = "+",
				color="k",
				alpha=0.8
			)
			plt.pause(0.0002)

	def onclose(self, event):
		self.disconnect()

	def end(self):
		self.disconnect()

		strategy_list = os.listdir("data/strategies/")
		strategy_nums = [np.int64(n[-4:]) for n in strategy_list if (name in n)]
		if ~os.path.exists(f"data/strategies/{name}"):
			name_num = 0
			if len(strategy_nums) > 0:
				name_num = max(strategy_nums)+1
			_name = name.replace(".", "").replace(" ", "_")
			save_path = f"data/strategies/{_name}_{str(name_num).zfill(4)}"
			os.mkdir(save_path)
			print(f"Thank you for playing! Your output is saved at: {save_path}")

		else:
			print("Error!")

	def disconnect(self):
		self.fig.canvas.mpl_disconnect(self.cid_button)
		self.fig.canvas.mpl_disconnect(self.cid_hover)
        #self.fig.canvas.mpl_disconnect(self.cid_key)
        #self.fig.canvas.mpl_disconnect(self.cid_close)

pattern = PatternCanvas(fig)
pattern.connect()
plt.show()

