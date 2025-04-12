import torch
from datetime import datetime, timedelta, timezone
import time
import sys
import os
import csv
repoPath = "/home/pi/Documents/"
sys.path.append(repoPath + "airQualPi/")
from circularTimeSeriesBuffer import CircularTimeSeriesBuffers

def write_worker(ctsb: CircularTimeSeriesBuffers, deviceDescriptor, colNames,
                   debug_lvl, exitSignal):
    # all this should do is save the last second
    def intTensorToDtList(tensor):
        return [datetime.fromtimestamp(ts_ns.item() / 1e9, tz=timezone.utc) for ts_ns in tensor]

    last_update_time = datetime.fromtimestamp(0, tz=timezone.utc)
    while True:
        if exitSignal[0] == 1:
            break
        
        st = datetime.now()
        secondsToWait = (1 - st.microsecond/1_000_000) + .0625 # 1/16 of a sec
        #print(f"writer: waiting {secondsToWait} till {st + timedelta(seconds=secondsToWait)}")
        time.sleep(secondsToWait)

        #check if there's new data but right

        lastBuffNum = ((ctsb.bn[0] + (ctsb.numBuffs[0]-1)) % ctsb.numBuffs[0]).clone()

        if ctsb.lengths[lastBuffNum][0] == 0:
                continue
        
        newTimestamps = intTensorToDtList(ctsb.time_buffers[lastBuffNum][:ctsb.lengths[lastBuffNum][0]])
        
        if newTimestamps[-1] <= last_update_time:
            continue
        last_update_time = newTimestamps[-1] 

        day_folder = repoPath + 'dayData/'
        if not os.path.exists(day_folder):
            os.mkdir(day_folder)

        hour_file_name = day_folder + "_".join(deviceDescriptor) + "_" +\
                        newTimestamps[0].strftime('%Y-%m-%dT%H%z') + '.csv'

        is_new_file = not os.path.exists(hour_file_name)
        
        # other popular types float64, int64, float32, int32
        with open(hour_file_name, "a", newline="") as f:
            writer = csv.writer(f)
            if is_new_file:  # Write headers only if file is new
                # print('writing cols!')
                print('new file! ' + hour_file_name)
                sys.stdout.flush()
                writer.writerow(colNames)
            
            for i, data in enumerate(ctsb.data_buffers[lastBuffNum][:ctsb.lengths[lastBuffNum][0]]):
                writer.writerow([newTimestamps[i].strftime('%Y-%m-%dT%H:%M:%S.%f%z')] + data.tolist())
        
        
            
        #honestly we could just have a cron job clean up and do the pandas conversions
    print('exiting writer for ', "_".join(deviceDescriptor))
