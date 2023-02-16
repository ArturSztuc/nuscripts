import os
from dataclasses import dataclass
import ROOT

@dataclass
class TPSetData:
    """
    Class for the received TP data
    """
    m_time_start: int
    m_adc_integral: int
    m_real_time: int

    def __str__(self):
        return f"{self.m_time_start}-{self.m_adc_integral}-{self.m_real_time}"

@dataclass
class TPDataRequest:
    """
    Class for the TP request from the TPBuffer
    """
    m_window_begin: int 
    m_window_end: int
    m_real_time: int

    def __str__(self):
        return f"{self.m_window_begin}-{self.m_window_end}-{self.m_real_time}"

@dataclass
class TPLatency:
    """
    Class for the TP latency data
    """
    m_tp_received: int
    m_tp_requested: int
    m_tp_latency: int

    def __str__(self):
        return f"{self.m_tp_received}-{self.m_tp_requested}-{self.m_tp_latency}"


def GetTPLatencies(_tp_received, _tp_requests):
    """
    Matches the received TPs with the TP requests from the TBuffer (triggered by
    the TriggerRecordBuilder), calculates the latency and stores/returns that in
    a vector of Latency objects.

    parameters:
        _tp_received: Vector of TPSetData objects
        _tp_requests: Vector of TPDataRequest objects
    """

    latencies = []
    iterator = 0
    for request in _tp_requests:
        for tp in _tp_received:
            # Save latency if within the window
            if (tp.m_time_start >= request.m_window_begin) and (tp.m_time_start <= request.m_window_end):
                latency = (request.m_real_time - tp.m_real_time)/1e9 # latencies were measured in nanoseconds
                #print(f"Latency: {latency}")
                latencies.append(TPLatency(tp.m_real_time, request.m_real_time, latency))
            # If above the window, look at the next request. TPs are sorted...
            elif tp.m_time_start > request.m_window_end:
                break
    return latencies

def GetNumberFromLine(_line, _text):
    """
    Gets a number from text line of text given the line and the text descriptor that
    corresponds to that number. E.g. "version_number: 5" will return 5 if
    provide "version_number:" in line parameter.

    parameters:
        _line: whole line of text for parsing to extract specific number
        _text: number's descriptior. E.g. "timestamp:" for "timestamp: 12132342"

    return:
        integer number corresponding to it's text descriptor
    """
    location = _line.find(_text)
    ret = _line[location:]
    ret = ret.replace(_text + " ", "")
    ret = ret.split(" ")
    #print("PRESPLIT: ", ret)
    ret = int(ret[0])
    #print("POSTSPLIT: ", ret)
    return int(ret)

def GetTPDataRequests(_file):
    """
    Retreives the TP request data from a file, saves and returns that data in
    an array of TPDataRequest objects.

    parameters:
        _file: Log file with all the trigger output

    return:
        A vector of the filled TPDataRequest objects
    """
    input_file = open(_file)
    input_data = input_file.readlines()
    input_file.close()

    data_requests = []
    for line in input_data:
        if("TPs being requested:" not in line):
            continue
        location = line.find("TPs being requested: ")
        line = (line[location:])

        window_begin = GetNumberFromLine(line, "window_begin:")
        window_end   = GetNumberFromLine(line, "window_end:")
        real_time    = GetNumberFromLine(line, "real_time:")
        data_requests.append(TPDataRequest(window_begin, window_end, real_time))

    print(f"Number of DataRequests requests: {len(data_requests)}")
    return data_requests

def GetTPSets(_file):
    """
    Retreives the TPs that were received by the Trigger app from a file, saves
    and returns that data in an array of TPSetData objects.

    parameters:
        _file: Log file with all the trigger output
    
    return:
        A vector of the filled TPSetData objects with TPSets' timestamps
    """
    input_file = open(_file)
    input_data = input_file.readlines()
    input_file.close()

    tp_sets = []
    for line in input_data:
        if("TPs Received." not in line):
            continue
        location = line.find("TPs Received.")
        line = (line[location:])

        time_start  = GetNumberFromLine(line, "time_start:")
        adc_integral= GetNumberFromLine(line, "ADC integral:")
        real_time   = GetNumberFromLine(line, "real_time:")

        tp_sets.append(TPSetData(time_start, adc_integral, real_time))

    print(f"Number of received TPSets: {len(tp_sets)}")
    return tp_sets 

def SetStyle():
    """
    Sets the plotting style.
    """
    ## Centre title
    ROOT.gROOT.GetStyle("Default").SetTitleAlign(22);
    ROOT.gROOT.GetStyle("Default").SetTitleX(.5);
    ROOT.gROOT.GetStyle("Default").SetTitleY(.95);
    ROOT.gROOT.GetStyle("Default").SetTitleBorderSize(0);
   
    ## set the background color to white
    ROOT.gROOT.GetStyle("Default").SetFillColor(10);
    ROOT.gROOT.GetStyle("Default").SetFrameFillColor(10);
    ROOT.gROOT.GetStyle("Default").SetCanvasColor(10);
    ROOT.gROOT.GetStyle("Default").SetPadColor(10);
    ROOT.gROOT.GetStyle("Default").SetTitleFillColor(0);
   
    ## Don't put a colored frame around the plots
    ROOT.gROOT.GetStyle("Default").SetFrameBorderMode(0);
    ROOT.gROOT.GetStyle("Default").SetCanvasBorderMode(0);
    ROOT.gROOT.GetStyle("Default").SetPadBorderMode(0);
   
    ## No border on legends
    ROOT.gROOT.GetStyle("Default").SetLegendBorderSize(0);
   
    ## Axis titles
    ROOT.gROOT.GetStyle("Default").SetTitleSize(.055, "xyz");
    ROOT.gROOT.GetStyle("Default").SetTitleOffset(.8, "xyz");
    # More space for y-axis to avoid clashing with big numbers
    ROOT.gROOT.GetStyle("Default").SetTitleOffset(.9, "y");
    # This applies the same settings to the overall plot title
    ROOT.gROOT.GetStyle("Default").SetTitleSize(.055, "");
    ROOT.gROOT.GetStyle("Default").SetTitleOffset(.8, "");
    # Axis labels (numbering)
    ROOT.gROOT.GetStyle("Default").SetLabelSize(.04, "xyz");
    ROOT.gROOT.GetStyle("Default").SetLabelOffset(.005, "xyz");
   
    ## Thicker lines
    ROOT.gROOT.GetStyle("Default").SetHistLineWidth(2);
    ROOT.gROOT.GetStyle("Default").SetFrameLineWidth(2);
    ROOT.gROOT.GetStyle("Default").SetFuncWidth(2);
   
    ## Set the number of tick marks to show
    ROOT.gROOT.GetStyle("Default").SetNdivisions(506, "xyz");
   
    ## Set the tick mark style
    ROOT.gROOT.GetStyle("Default").SetPadTickX(1);
    ROOT.gROOT.GetStyle("Default").SetPadTickY(1);
   
    ## Fonts
    kNovaFont = 42;
    ROOT.gROOT.GetStyle("Default").SetStatFont(kNovaFont);
    ROOT.gROOT.GetStyle("Default").SetLabelFont(kNovaFont, "xyz");
    ROOT.gROOT.GetStyle("Default").SetTitleFont(kNovaFont, "xyz");
    ROOT.gROOT.GetStyle("Default").SetTitleFont(kNovaFont, "")#  Apply same setting to plot titles
    ROOT.gROOT.GetStyle("Default").SetTextFont(kNovaFont);
    ROOT.gROOT.GetStyle("Default").SetLegendFont(kNovaFont);
   
    ROOT.gROOT.SetStyle("Default");

def Plot(_latencies, _output):
    """
    Takes the vector of latencies, output name/folder, and generates/saves the
    latency plots.

    parameters:
        latencies: vector of TPLatency objects
        output: optional output folder/file name
    """

    # Sets the general stylistics (based on NOvA)
    SetStyle()
    ROOT.gROOT.SetBatch(True)

    # Sort the latencies and find min/max
    print("Sorting received TPs!")
    _latencies.sort(key=lambda x: x.m_tp_latency)
    minimum = _latencies[0].m_tp_latency
    maximum = _latencies[-1].m_tp_latency
    print(f"Minimum: {minimum}")
    print(f"Maximum: {maximum}")

    # Create and fill the latencies histogram(s?)
    histogram = ROOT.TH1D("", ";#Delta t (s);Number of TPs;", 100, float(minimum), float(maximum))
    for lat in _latencies:
        histogram.Fill(lat.m_tp_latency)
    
    # Save the histograms
    canvas = ROOT.TCanvas("canvas")
    canvas.cd()
    histogram.Draw()
    canvas.SaveAs(_output + "output.png")

def main(_file, _output):
    print("Extracting the TP requests")
    tp_requests = GetTPDataRequests(_file)

    print("Extracting the received TPs")
    tp_received = GetTPSets(_file)

    print(f"Last TP received: {tp_received[-1].m_real_time}")
    print(f"Last TP request : {tp_requests[-1].m_real_time}")

    print("Sorting TP requests!")
    tp_requests.sort(key=lambda x: x.m_window_begin)

    print("Sorting received TPs!")
    tp_received.sort(key=lambda x: x.m_time_start)

    print("Filling the TP latencies!")
    latencies = GetTPLatencies(tp_received, tp_requests)
    
    print("Plot latencies!")
    Plot(latencies, _output)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sterilize DAQ log to get the latency timestamps")

    # TODO: Add user-defined minimum and maximum?
    parser.add_argument('-f' '--file',   dest='file',     help='DAQ log file input')
    parser.add_argument('-o' '--output', dest='output',   default='', help='Plot output')

    args = parser.parse_args()
    main(args.file, args.output)