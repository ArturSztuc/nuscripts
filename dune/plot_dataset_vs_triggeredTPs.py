from matplotlib import pyplot as plt
import numpy as np
import argparse


# Setup plot
fig, axs = plt.subplots(2, 1, sharey=True, sharex=True)
axs.ravel()
title= "Offline Triggered TPs - VDCB Run 020427: 12 Links SW TPG TPs"
legend_properties = {'weight': 'bold'}

# Read in offline dataset
data = np.genfromtxt("../data/tps/offline_tp_datasets/run_020472_tps_2seconds.txt", delimiter=' ')
data = data.transpose()

start_time = data[0][:]
time_shift = start_time[0]
data_channel = data[3][:]
adc_sum = data[4][:]
start_time = start_time - time_shift
start_time *= 16e-9

triggered_tps = np.genfromtxt("../data/tps/triggered_tps/run_020472_triggered_tp_windows.txt", delimiter=' ')
triggered_tps = triggered_tps.transpose()

trig_start_time = triggered_tps[0][:]
# trig_shift = trig_start_time[0]
trig_start_time = trig_start_time - time_shift
trig_start_time *= 16e-9
trig_channel = triggered_tps[3][:]

channels = [data_channel, trig_channel]
times = [start_time, trig_start_time]
labels = ["Dataset", "Triggered TPs"]

for i in range(2):
    axs[i].scatter(times[i], channels[i], s =2, label=labels[i])
    # axs[i].legend()
    if i == 0:
        axs[i].scatter(times[i+1], channels[i+1], s=5, label=labels[i+1], color='r')

fig.suptitle("Dataset TPs vs Triggered TPs", fontweight="bold", fontsize=20)
# fig.set_xlabel("Relative Time - Seconds")
# fig.set_ylabel("Offline Channel ID")
plt.show()






# print("Plotting and saving a event display of TPs.")
# label="Input TPs - Event Display"
# im = fig.scatter(start_time, channel, s=20, label=label, c=adc_sum, vmax=np.max(adc_sum)/20)
# fig.set_xlabel("Relative Time (s)", fontweight='bold')
# fig.set_ylabel("Offline Channel ID", fontweight='bold')
# fig.set_title(title, fontweight='bold')
# fig.legend(prop=legend_properties, loc="upper right")
# file_name = "../output/run_" + str(run) + "_tp_event_display.png"
# plt.savefig(file_name, format="png")
# plt.show()