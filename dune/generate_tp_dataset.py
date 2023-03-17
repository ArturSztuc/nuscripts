# Script to generate a dataset of TPs across all channels. This needs to be done
# since the TPStream files are quite blocky, and don't guarantee a continuous time ordered
# representation of the TPs seen by the trigger system in online runs. The output can be
# fed directly to the TP replay app in DUNE DAQ, for offline triggering studies.
from matplotlib import pyplot as plt
import numpy as np
import argparse


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


def read_data_file(file):
    """
    Read in the data file of trigger primitives, order them
    by start time, as we expect the trigger system to see them.
    Return the ordered data set for dataset making.
    :param file: Input TPs extracted from TPStream file.
    :return: data - numpy array representing the full input file, time ordered
    """
    print("Grabbing TP info from input file.")
    data = np.genfromtxt(file, delimiter=' ')
    if not check_time_ordering(data[:, 0]):
        print("Input is not time ordered. This is kind of expected, ordering now...")
        data = data[data[:, 0].argsort()]
    data = data.transpose()
    return data


def construct_dataset(data, out, num_seconds):
    """
    This part does the heavy lifting, writing each TP as one line
    to the output file. The format is displayed below, what the replay
    app and triggerprimitivemaker in DUNE DAQ expects.
    :param data: The time ordered numpy array read in from the input file.
    :param out: The name of the output file.
    :param num_seconds: The number of seconds we'll attempt to extract from the input.
    :return:
    """
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

    print("Attempting to write ", num_seconds, " seconds of TP dataset for offline trigger use. The output is in the"
          + " following format, which can be fed directly to the trigger replay app:\n"
          "<start_time> <time_over_threshold> <time_peak> <channel> <adc_integral> <adc_peak> <det_id> <type>")
    f = open(out, 'w')
    for i, st in enumerate(start_time_seconds):
        if st < num_seconds:
            info = str(int(start_time[i])) + " " + str(int(time_over[i])) + " " + str(int(time_peak[i])) +\
                   " " + str(int(channel[i])) + " " + str(int(adc_sum[i])) + " " + str(int(adc_peak[i])) +\
                   " " + str(int(det_id[i])) + " " + str(int(type[i])) + "\n"
            f.write(info)
    f.close()


def plot_constructed_dataset(out, run):
    """
    Read in the constructed file clean, and plot the results.
    Aim here is to help user see that the constructed dataset looks
    as expected before feeding to the replay app / analysing.
    :param out: The output dataset we have constructed in this script.
    :param run: The run number, read from the input arguments to this script.
    :return:
    """
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
    fig.scatter(start_time_seconds, channel, s=1, label=label, c=adc_sum, vmax=np.max(adc_sum)/10)
    fig.set_xlabel("Relative Time (s)", fontweight='bold')
    fig.set_ylabel("Offline Channel ID", fontweight='bold')
    fig.set_title(title, fontweight='bold')
    fig.legend(prop=legend_properties, loc="upper right")
    file_name = "run_" + str(run) + "_tp_event_display.png"
    plt.savefig(file_name, format="png")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Accept extracted TPs from TPStream file and produce a dataset for offline replay")
    parser.add_argument('-r' '--run', dest='run', default="0xxxxx", help='Run number in format 0xxxxx')
    parser.add_argument('-f' '--file', dest='file', help='Extracted TPs file from the TPWriter app')
    parser.add_argument('-o' '--out', dest='out', default="offline_tp_dataset.txt", help='Output file name')
    parser.add_argument('-n' '--num_tps', dest='num_tps', default=500000,
                        help='Number of TPs from online run to obtain')
    parser.add_argument('-s' '--seconds', dest='num_secs', default=5,
                        help='Number of TPs from online run to obtain. Default is to try 5 seconds.')
    parser.add_argument('-p', '--plot_output', action="store_true",
                        help="Add this flag to output a png event display of the constructed dataset")

    args = parser.parse_args()
    run = args.run
    file = args.file
    out = args.out
    n = int(args.num_tps)
    plot_ds = args.plot_output
    num_seconds = int(args.num_secs)

    data = read_data_file(file)
    # Quick check that we have enough TPs in the input. Revert to default otherwise.
    if len(data[0][:]) < int(n):
        print("Requested to read more TPs that we have infile, reverting to total TPs.")
        n = len(data[0][:])

    construct_dataset(data, out, num_seconds)
    if plot_ds:
        plot_constructed_dataset(out, run)
    print("\nOffline TP dataset complete!\n")

