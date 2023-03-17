from matplotlib import pyplot as plt
import numpy as np
import argparse

# Script to generate a dataset of TPs across all channels. This needs to be done
# since the TPStream files are quite blocky, and don't guarantee a continuous time ordered
# representation of the TPs seen by the trigger system in online runs.


# Check the time ordering of a list of times.
def check_time_ordering(list):
    ordered = True
    print("Checking TP time ordering...")
    previous = 0
    for start_time in list:
        if start_time < previous:
            ordered = False
        previous = start_time
    return ordered


parser = argparse.ArgumentParser(description="Accept extracted TPs from TPStream file and produce a dataset for offline replay.")
parser.add_argument('-r' '--run', dest='run', default="0xxxxx", help='Run number in format 0xxxxx')
parser.add_argument('-f' '--file', dest='file', help='Extracted TPs file from the TPWriter app.')
parser.add_argument('-o' '--out', dest='out', default="offline_tp_dataset.txt", help='Output file name.')
parser.add_argument('-n' '--num_tps', dest='num_tps', default=500000, help='Number of TPs from online run to obtain.')
parser.add_argument('-s' '--seconds', dest='num_secs', default=5, help='Number of TPs from online run to obtain. Default is to try 5')

args = parser.parse_args()
run = args.run
file = args.file
out = args.out
n = int(args.num_tps)
num_seconds = int(args.num_secs)

print("Grabbing TP info from input file...")
data = np.genfromtxt(file, delimiter=' ')
data = data[data[:, 0].argsort()]
data = data.transpose()

if len(data[0][:]) < int(n):
 print("Requested to read more TPs that we have infile, reverting to default.")
 n = 100000

print("Reading in ", n, " TPs...")
start_time = data[0][:n]
time_shift = start_time[0]
start_time = start_time - time_shift
time_over = data[1][:n]
time_peak = data[2][:n] - time_shift
channel = data[3][:n]
adc_sum = data[4][:n]
adc_peak = data[5][:n]
type = data[6][:n]
det_id = data[7][:n]

# Also get the times in seconds, more understandable for us making a dataset.
start_time_seconds = start_time*16e-9

print("Attempting to write ", num_seconds, " seconds of TP dataset for offline trigger use. The output is in the following format, which can be fed directly to"
      " the trigger replay app:\n"
      "<start_time> <time_over_threshold> <time_peak> <channel> <adc_integral> <adc_peak> <det_id> <type>")
f = open(out, 'w')
for i, st in enumerate(start_time_seconds):
    if st < num_seconds:
        info = str(int(start_time[i])) + " " + str(int(time_over[i])) + " " + str(int(time_peak[i])) +\
               " " + str(int(channel[i])) + " " + str(int(adc_sum[i])) + " " + str(int(adc_peak[i])) +\
               " " + str(int(det_id[i])) + " " + str(int(type[i])) + "\n"
        f.write(info)
f.close()


# Plot and save a quick TP event display for checking the dataset.
# Read in the generated dataset, clean.
data = np.genfromtxt(out, delimiter=' ')
data = data.transpose()
start_time_seconds = data[0][:]*16e-9
channel = data[3][:]
adc_sum = data[4][:n]

# Plot the thing.
fig = plt.subplot(111)
title= "VDCB Run " + str(run) + ": 12 Links SW TPG TPs"
legend_properties = {'weight': 'bold'}
print("Plotting and saving a event display of extracted TPs dataset.")
label="Input TPs - Event Display"
im = fig.scatter(start_time_seconds, channel, s=1, label=label, c=adc_sum, vmax=np.max(adc_sum)/10)
fig.set_xlabel("Relative Time (s)", fontweight='bold')
fig.set_ylabel("Offline Channel ID", fontweight='bold')
fig.set_title(title, fontweight='bold')
fig.legend(prop=legend_properties, loc="upper right")
file_name = "run_" + str(run) + "_tp_event_display.png"
plt.savefig(file_name, format="png")
print("\nOffline TP dataset complete!")