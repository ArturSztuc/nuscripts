import os
from tqdm import tqdm
from dataclasses import dataclass
import ROOT

# TODO: Change these @dataclasses to numpy matrices?

class TPSetData:
    """
    Class for the received TP data
    """
    def __init__(self, _time_start, _adc_integral, _time_intrigger, _time_inbuffer):
        self.m_time_start       = int(_time_start)
        self.m_adc_integral     = int(_adc_integral)
        self.m_time_intrigger   = int(_time_intrigger)
        self.m_time_inbuffer    = int(_time_inbuffer)
        self.m_latency_tp_received_to_buffered = (_time_inbuffer - _time_intrigger)/1e9

class TPDataRequest:
    """
    Class for the TP request from the TPBuffer
    """
    def __init__(self, _window_begin, _window_end, _time_received, _time_handled):
        self.m_window_begin = int(_window_begin)
        self.m_window_end   = int(_window_end)
        self.m_time_received= int(_time_received)
        self.m_time_handled = int(_time_handled)
        self.m_latency_dr_received_to_handled = (_time_handled - _time_received)/1e9

@dataclass
class TPLatency:
    """
    Class for the TP latency data
    """
    m_latency_tptrigger_to_drhandled: int
    m_latency_tptrigger_to_drreceived: int
    m_latency_tpbuffered_to_drreceived: int

    def __str__(self):
        return f"{self.m_latency_tptrigger_to_drhandled}-{self.m_latency_tptrigger_to_drreceived}"

@dataclass
class MLTDRLatency:
    """
    This is dumb, but that's how I have to do it for now because of how the plotting script is written...
    TODO: Change all of this to numpy arrays
    """
    m_latency_td_to_dr: int

@dataclass
class TPMLTLatency:
    """
    Data class holding the TP->TR latencies
    """
    m_latency_tptrigger_to_tdsent: int
    m_latency_tpbuffered_to_tdsent: int

@dataclass
class MLTTriggerDecision:
    """
    Class for the MLT latency data
    """
    #m_tpsets: int
    #m_tpdatarequests: int
    m_readout_start: int
    m_readout_end: int
    m_latency_mlt_td_to_dfo: int

    def __str__(self):
        return f"{self.m_readout_start}-{self.m_readout_start}"

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
    for request in tqdm(_tp_requests):
        for tp in _tp_received:
            # Save latency if within the window
            if (tp.m_time_start >= request.m_window_begin) and (tp.m_time_start <= request.m_window_end):
                latency_tptrigger_to_drhandled = (request.m_time_handled - tp.m_time_intrigger)/1e9
                latency_tptrigger_to_drreceived = (request.m_time_received - tp.m_time_intrigger)/1e9
                latency_tpbuffered_to_drreceived = (request.m_time_received - tp.m_time_inbuffer)/1e9
                #print(f"Latency: {latency}")
                latencies.append(TPLatency(#tp.m_real_time, request.m_real_time,
                                           latency_tptrigger_to_drhandled,
                                           latency_tptrigger_to_drreceived,
                                           latency_tpbuffered_to_drreceived))
            # If above the window, look at the next request. TPs are sorted...
            elif tp.m_time_start > request.m_window_end:
                break
    return latencies

def GetTP_to_MLT(_trigger_decisions, _tp_requests):
    """
    Matches the received TPs with the Trigger Decisions sent from the
    ModuleLevelTrigger, calculates the latency and stores/returns that in a
    vector of Latency objects.

    parameters:
        _trigger_decisions: Vector of MLTTriggerDecision objects
        _tp_requests: Vector of TPDataRequest objects
    """
    latencies = []
    for td in tqdm(_trigger_decisions):
        for tp in _tp_requests:
            if (tp.m_time_start >= td.m_readout_start) and (tp.m_time_start <= td.m_readout_end):
                latency_intrigger_to_tdsent = (td.m_latency_mlt_td_to_dfo - tp.m_time_intrigger )/1e9
                latency_inbuffer_to_tdsent  = (td.m_latency_mlt_td_to_dfo - tp.m_time_inbuffer  )/1e9
                latencies.append(TPMLTLatency(latency_intrigger_to_tdsent, latency_inbuffer_to_tdsent))
            elif tp.m_time_start > td.m_readout_end:
                break
    return latencies

def GetMLT_to_DRReceivedLatencies(_trigger_decisions, _data_requests):
    """
    Matches the TriggerDecisions from the ModuleLevelTrigger with the
    DataRequests received by the TPBufer, calculates the latencies and
    stores/returns that in a vector of Latency objects.

    parameters:
        _trigger_decisions: Vector of MLTTriggerDecision objects
        _tp_requests: Vector of DataRequest objects
    """
    latencies = []
    for td in tqdm(_trigger_decisions):
        for dr in _data_requests:
            if (td.m_readout_start == dr.m_window_begin) and (td.m_readout_end == dr.m_window_end):
                latency = (dr.m_time_received - td.m_latency_mlt_td_to_dfo)/1e9
                latencies.append(MLTDRLatency(latency))
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

def GetObjectVector(_file, _prefix, _token_list, _ObjectType):
    # Open the file
    input_file = open(_file)
    input_data = input_file.readlines()
    input_file.close()

    # Debugging...
    print(f'Getting the following objects:\n  _file: {_file}\n  _prefix: {_prefix}\n  _token_list: {_token_list}\n  _ObjectType: {_ObjectType}')
    
    objects = []
    for line in input_data:
        # Only continue if the prefix is right
        if(_prefix not in line):
            continue

        # Extract the line
        location = line.find(_prefix)
        line = (line[location:])

        # Fill data for each token
        data = []
        for token in _token_list:
            data.append(GetNumberFromLine(line, token))

        # Create the new object and append to our array
        objects.append(_ObjectType(*data))

    # Return array of objects
    return objects

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

def DrawAndSave(histogram, name):
    # Save the histograms
    canvas = ROOT.TCanvas("canvas")
    canvas.cd()
    histogram.Draw()
    canvas.SaveAs(name)

def Plot(_vector_objects, _data_handle_name, _output_name, _histogram_title):
    """
    Plots a vector of objects' data member into a histogram and saves it into an
    output .png file.

    prameters:
        _vector_objects: vector of objects for plotting
        _data_handle_name: the exact name of the object's class data member to plot
        _output_name: the full output name
        _histogram_title: histogram title with the axis titles, in ROOT format
    """
    # Sets the general stylistics (based on NOvA)
    SetStyle()
    ROOT.gROOT.SetBatch(True)

    # Sort the latencies and find min/max
    print("Sorting received TPs!")
    _vector_objects.sort(key=lambda x: vars(x)[_data_handle_name])
    minimum = vars(_vector_objects[0])[_data_handle_name]
    maximum = vars(_vector_objects[-1])[_data_handle_name]

    print(f"Minimum: {minimum}")
    print(f"Maximum: {maximum}")

    # Create and fill the latencies histogram
    histogram= ROOT.TH1D("", _histogram_title, 100, float(minimum), float(maximum))
    for obj in _vector_objects:
        histogram.Fill(vars(obj)[_data_handle_name])

    DrawAndSave(histogram, _output_name)

def main(_file, _output):
    # Extracting Data Requests
    print("Extracting the DataRequest objects")

    tp_requests = GetObjectVector(_file, 'TPs Requested:',
                                  ['window_begin:', 'window_end:', 'real_time_req:', 'real_time_han:'],
                                  TPDataRequest)

    #tp_requests = GetTPDataRequests(_file)

    print("Plotting the DataRequest latency")
    Plot(tp_requests, 
         "m_latency_dr_received_to_handled",
         _output + "latency_DRReceived_to_DRHandled.png",
         "Latency: DataRequest Received to DataRequest handled;#Delta t(s);Number of TPs")

    # Extracting ModuleLevelTrigger TriggerDecisions
    print("Extracting the MLTTriggerDecision objects")

    td_sent = GetObjectVector(_file, 'MLT TD Sent:',
                              ['readout_start:', 'readout_end:', 'time_td_sent:'],
                              MLTTriggerDecision)


    #td_sent = GetMLTTriggerDecisions(_file)
    print("Sorting MLTTriggerDecision objects")
    td_sent.sort(key=lambda x: x.m_readout_start)

    # Extracting the received and buffered TPSets
    print("Extracting the received TPs")
    tp_received = GetObjectVector(_file, 'TPs Received.',
                                  ['time_start:', 'ADC integral:', 'real_time_in:', 'real_time_buff:'],
                                  TPSetData)

    #tp_received = GetTPSets(_file)

    print("Plotting the TP objects")
    Plot(tp_received, 
         "m_latency_tp_received_to_buffered",
         _output + "latency_TPReceived_to_TPBuffered.png",
         "Latency: TPSet Received to TPSet buffered;#Delta t(s);Number of TPs")

    print("Sorting TP requests!")
    tp_requests.sort(key=lambda x: x.m_window_begin)

    print("Sorting received TPs!")
    tp_received.sort(key=lambda x: x.m_time_start)

    # Extrating the TriggerDecisions from the ModuleLevelTrigger
    print("Filling the MLT Trigger decisions to DataRequestes received latencies!")
    mlt_to_drreceived_latencies = GetMLT_to_DRReceivedLatencies(td_sent, tp_requests)
    Plot(mlt_to_drreceived_latencies, 
         "m_latency_td_to_dr",
         _output + "latency_TriggerDecision_to_DRReceived.png",
         "Latency: MLT Trigger Decision Sent to DataRequest Received;#Delta t(s);Number of DataRequests")

    print("Filling the TPReceived & buffered to MLT trigger decision sent!")
    tp_to_mlt_latencues = GetTP_to_MLT(td_sent, tp_received)

    # Plotting the rest of the latencies
    Plot(tp_to_mlt_latencues, 
         "m_latency_tptrigger_to_tdsent",
         _output + "latency_TPReceived_to_TDSent.png",
         "Latency: TPSet Received to MLT Trigger Decision Sent;#Delta t(s);Number of TPs")

    Plot(tp_to_mlt_latencues, 
         "m_latency_tpbuffered_to_tdsent",
         _output + "latency_TPBuffered_to_TDSent.png",
         "Latency: TPSet Buffered to MLT Trigger Decision Sent;#Delta t(s);Number of TPs")

    print("Filling the TP latencies!")
    latencies = GetTPLatencies(tp_received, tp_requests)
    Plot(latencies, 
         "m_latency_tptrigger_to_drhandled",
         _output + "latency_TPReceived_to_DRHandled.png",
         "Latency: TPSet Received to DataRequest Handled;#Delta t(s);Number of TPs")
    Plot(latencies, 
         "m_latency_tptrigger_to_drreceived",
         _output + "latency_TPReceived_to_DRReceived.png",
         "Latency: TPSet Received to DataRequest Received;#Delta t(s);Number of TPs")
    Plot(latencies, 
         "m_latency_tpbuffered_to_drreceived",
         _output + "latency_TPBuffered_to_DRReceived.png",
         "Latency: TPSet Buffered to DataRequest Received;#Delta t(s);Number of TPs")
    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sterilize DAQ log to get the latency timestamps")

    # TODO: Add user-defined minimum and maximum?
    parser.add_argument('-f' '--file',   dest='file',     help='DAQ log file input')
    parser.add_argument('-o' '--output', dest='output',   default='', help='Plot output')

    args = parser.parse_args()
    main(args.file, args.output)
