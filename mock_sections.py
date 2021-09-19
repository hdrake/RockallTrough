
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os.path
import pandas as pd

from utils import *


# Input parameters
cast_duration = 5.
ship_speed = 5./86400.
show_solution = False

#
ds = load_all_data()

df = pd.DataFrame({"castnum": [], "time": [], "Z":  [], "dZ": [], "c": [] })

fig = plt.figure(figsize=(13, 7))
ax = plt.axes([0.075, 0.2, 0.595, 0.75])

pc = ds["c_Zint"].isel(time=-1).plot(
    ax=ax, alpha=1., cmap = plt.get_cmap("Purples"),
    norm = matplotlib.colors.LogNorm(vmin=3e-12, vmax=3e-9)
)
pc.colorbar.remove()
ds["Depth"].plot.contour(ax=ax, levels=np.arange(-500, 4000, 500), cmap="Greys", alpha=0.6)
ax.set_xlabel("longitude [degrees east]")
ax.set_ylabel("latitude [degrees north]")
release = (-11.895, 54.233)
ax.plot(release[0], release[1], "C3x", markersize=13, markeredgewidth=2.75, markeredgecolor="C3")
ann = ax.annotate(f"elapsed time: 0.0 days", xy=(-12.5, 53.6), fontsize=14.)
hoverline = ax.plot([],[], "C1-", alpha=0.4, linewidth=1.2)
hoverplot = ax.plot([],[], markersize=7, marker = "o", color="k", alpha=0.8)

sax = plt.axes([0.65, 0.2, 0.32, 0.75])
sax.set_title("")
sax.set_xlabel(r"tracer concentration [kg/m$^{3}$]")
sax.set_ylabel(r"depth [m]")

cax = plt.axes([0.075, 0.085, 0.4775, 0.03])
plt.colorbar(pc, cax=cax, label=r"vertically-integrated tracer [kg / m$^{2}$]", orientation="horizontal")
pc.set(alpha=0.)

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

ax.set_title(f"You have {N} casts left!", loc="left", fontsize=14)
ax.grid(alpha=0.2)
ax.set_title("")
ax.set_ylim(53.5, 57)
ax.set_xlim(-15.2, -10.305)
ax.set_yticks(np.arange(53.5, 57.5, 0.5))
ax.set_yticklabels(np.arange(53.5, 57.5, 0.5))

sax.set_title("")
sax.set_xlim([0, 1e-11])
sax.set_ylim(-2500., -500.)

class PatternCanvas:
	def __init__(self, fig):
		self.fig = fig
		self.ax = ax
		self.sax = sax
		self.cax = cax
		self.paused = False
		self.logscale = False

		self.last_xy = release

		self.cast_num = 0
		self.elapsed_time = 0.
		self.name = name
		self.df = df

	def connect(self):
		self.cid_button = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
		self.cid_key = self.fig.canvas.mpl_connect('key_press_event', self.onkey)
		self.cid_close = self.fig.canvas.mpl_connect('close_event', self.onclose)
		self.cid_hover = self.fig.canvas.mpl_connect("motion_notify_event", self.onhover)
	
	# Click event handler: toggle cells
	def onclick(self, event):
		if (event.inaxes == self.ax) and (~self.paused):
			x = event.xdata
			y = event.ydata
			self.cast_num += 1
			self.elapsed_time += cast_duration + ship_speed*self.steaming_distance(x,y)
			print(f"Cast {self.cast_num}: ({np.round(x,3)}, {np.round(y,3)})")

			ann.set_text(f"elapsed time: {round(self.elapsed_time/24.,1)} days")
			
			sample = ds.isel(time=-1).sel(XC=x, YC=y, method="nearest")
			self.ax.scatter(
				sample["XC"],
				sample["YC"],
				s = 60,
				c = sample["c_Zint"],
				cmap = plt.get_cmap("Purples"),
				marker = "o",
				edgecolors = "k",
				linewidths = 0.75,
				norm = matplotlib.colors.LogNorm(vmin=3e-12, vmax=3e-9)
			)
			ax.plot([self.last_xy[0], x],[self.last_xy[1], y], "C1-", alpha=0.6, linewidth=1.25)
			sample["c"].plot(ax=self.sax, y="Z")
			self.sax.set_title("")
			self.sax.set_xlabel(r"tracer concentration [kg/m$^{3}$]")
			self.sax.set_ylabel(r"depth [m]")

			self.ax.set_title(f"You have {N-self.cast_num} casts left!", loc="left", fontsize=14)

			sample_dict = {
				"castnum": self.cast_num*xr.ones_like(sample["c"], dtype="int64"),
				"time": sample["time"]*xr.ones_like(sample["c"]),
				"Z": sample["Z"],
				"dZ": sample["drF"],
				"c": sample["c"]
			}
			sample_df = pd.DataFrame(data=sample_dict)
			self.df = self.df.append(sample_df)
			self.last_xy = (x,y)
			plt.pause(0.001)

			if self.cast_num==N:
				self.end()
				plt.pause(0.002)

	def onhover(self, event):
		if event.inaxes == self.ax:
			self.hovering = (event.xdata, event.ydata)
			
			hoverplot[0].set_data([self.hovering[0], self.hovering[1]])
			hoverline[0].set_data([self.last_xy[0], self.hovering[0]],[self.last_xy[1], self.hovering[1]])
			plt.pause(0.00002)

	def onkey(self, event):
		if event.key == "p":
			if self.paused:
				print("Resuming.")
			else:
				print("Pausing.")
			self.paused = ~self.paused
		if event.key == "u":
			if ~self.logscale:
				sax.set_xscale("log")
				sax.set_xlim([1e-15, 1e-11])
			else:
				sax.set_xscale("linear")
				sax.set_xlim([0, 1e-11])
			self.logscale = ~self.logscale
			plt.draw()

	def onclose(self, event):
		self.disconnect()

	def end(self):
		if show_solution:
			pc.set(alpha=1.0)
		try:
			hoverline[0].remove()
			hoverplot[0].remove()
		except:
			pass
		self.disconnect()

		_name = name.replace(".", "").replace(" ", "_")
		strategy_list = os.listdir("data/strategies/")
		strategy_nums = [np.int64(n[-4:]) for n in strategy_list if (_name in n)]
		if ~os.path.exists(f"data/strategies/{_name}"):
			name_num = 0
			if len(strategy_nums) > 0:
				name_num = max(strategy_nums)+1
			
			save_path = f"data/strategies/{_name}_{str(name_num).zfill(4)}"
			os.mkdir(save_path)
			print(f"Thank you for playing! Your output is saved at: {save_path}")

			# Save ouputs
			self.df.to_csv(f"{save_path}/samples.csv")
			self.fig.savefig(f"{save_path}/samples.png", dpi=100., bbox_inches="tight")

		else:
			print("Error!")

	def steaming_distance(self, x, y):
		Rearth = 6.378E6   # radius of Earth in meters
		Δx = np.deg2rad(x-self.last_xy[0])*Rearth*np.cos(np.deg2rad((y + self.last_xy[1])/2))
		Δy = np.deg2rad(y-self.last_xy[1])*Rearth
		return np.sqrt(Δx**2 + Δy**2)

	def disconnect(self):
		self.fig.canvas.mpl_disconnect(self.cid_button)
		self.fig.canvas.mpl_disconnect(self.cid_close)
		self.fig.canvas.mpl_disconnect(self.cid_hover)

pattern = PatternCanvas(fig)
pattern.connect()
plt.show()

