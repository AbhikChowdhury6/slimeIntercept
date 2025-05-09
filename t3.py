from scapy.all import sniff, UDP, IP
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import time
import select
import copy

import torch
import torch.multiprocessing as mp

import sys
import os
repoPath = "/home/pi/Documents/"
sys.path.append(repoPath + "slimeIntercept/")
from sensor import Sensor
from sniff import SNIFFER

from icecream import ic
# so what do I want to do here
# i'd like to have a reference for the ip's
# add the ip's I want to the capture, with the mounting location
# if the bvh works i may not even need rotation hmmm

#but for now let's make a couple of device descriptors and column names
instance_name = 'testpi'

bno085_sd = {
    "abno085": {
        'class_name':'aBNO085',
        'responsiblePartyName': 'abhik',
        'instanceName': instance_name,
        'manufacturer': 'slimevr-CEVA',
        'deviceName': "slime-bno085",
        'sensors': {
            'linaccel-ms2': {
                'hz': 2**7,
                'col_names': ['sampleDT!int64!datetime64[ns]!audelayhz7',
                              'linaccelx-ms2!float32!float32!afloat10',
                              'linaccely-ms2!float32!float32!afloat10',
                              'linaccelz-ms2!float32!float32!afloat10']
            },
            'quat': {
                'hz': 2**7,
                'col_names': ['sampleDT!int64!datetime64[ns]!audelayhz7', 
                              'quatw!float32!float32!aboundedfloat11',
                              'quatx!float32!float32!aboundedfloat11',
                              'quaty!float32!float32!aboundedfloat11',
                              'quatz!float32!float32!aboundedfloat11']
            }
        }
    }
}



#make a separate sniff prcess that writes to a shared buffer for slime to read
class slime:
    def __init__(self, descriptor, debug_lvl, exit_signal=None):
        print(descriptor)

        IPS = {'192.168.1.10': (0,'right-upper-arm'), 
               '192.168.1.19': (1,'left-upper-arm'),
               '192.168.1.36': (2,'right-thigh'),
               '192.168.1.96': (3,'left-thigh'),
               '192.168.1.117': (4,'chest')}

        self.ts_buffer = torch.zeros((len(IPS), 1), dtype=torch.int64).share_memory_()
        self.accel_buffer = torch.zeros((len(IPS), 3), dtype=torch.float32).share_memory_()
        self.quat_buffer = torch.zeros((len(IPS), 4), dtype=torch.float32).share_memory_()

        print('starting a ' + descriptor['deviceName'] + '!')
        self.sniff_process = mp.Process(target=SNIFFER, args=(IPS, 
                                                              self.ts_buffer,
                                                              self.accel_buffer,
                                                              self.quat_buffer,
                                                              debug_lvl, 
                                                              exit_signal))
        self.sniff_process.start()

        # the name of the ips would actually be appended to the data type and not the instance
        # so we would generate the retrieve datas dict and the sensor descriptors based on IPS

        #let's start with the sensor descriptors
        sensor_descriptors = {}
        base_sds = descriptor['sensors']
        for ip in IPS:
            for sd in base_sds:
                #change the name
                new_data_type = IPS[ip][1] + '-' + sd
                #also change the col_names
                new_col_names = []
                for cn in base_sds[sd]['col_names']:
                    if cn.split('!')[0] == 'sampleDT':
                        new_col_names.append(cn)
                        continue
                    new_col_names.append(IPS[ip][1] + '-' + cn)
                
                sensor_descriptors[new_data_type] = copy.deepcopy(base_sds[sd])
                sensor_descriptors[new_data_type]['col_names'] = new_col_names
                #add a new field for this sensor
                sensor_descriptors[new_data_type]['buff_idx'] = IPS[ip][0]
        
        ic(sensor_descriptors)


        # now each of the keys in sensor descriptors make a retirve data function
        retrieve_datas = {}
        for sd in sensor_descriptors:
            desc = sd.split('-')[-1][:3]
            ipidx = sensor_descriptors[sd]['buff_idx']
            if desc == 'ms2':
                retrieve_datas[sd] = lambda ipidx=ipidx: self.accel_buffer[ipidx]
            elif desc == 'qua':
                retrieve_datas[sd] = lambda ipidx=ipidx: self.quat_buffer[ipidx]
            else: 
                print("don't recognize the data type")

        is_readies = {}
        for sd in sensor_descriptors:
            ipidx = sensor_descriptors[sd]['buff_idx']
            #print(ipidx)
            def is_ready(ipidx=ipidx):
                #check if it's fresh
                #print(ipidx)
                fts =  datetime.fromtimestamp(int(self.ts_buffer[ipidx]) / 1e9, tz=timezone.utc) \
                            + timedelta(seconds=1/128)
                now = datetime.now().astimezone(ZoneInfo("UTC"))
                #ic(ipidx, fts - now)
                #sys.stdout.flush()
                return now < fts
            is_readies[sd] = is_ready


        self.sensors = []
        for s in sensor_descriptors:
            dd = [descriptor['responsiblePartyName'],
                descriptor['instanceName'],
                descriptor['manufacturer'],
                descriptor['deviceName'],
                s,
                'internal']
            sen = Sensor(sensor_descriptors[s], retrieve_datas[s], is_readies[s], dd, debug_lvl, exit_signal)
            self.sensors.append(sen)



#alright now all that's left before testing is to init a slime 
#add their sensors to a list
# and check call read data with the right cadence
exit_signal = torch.zeros(1, dtype=torch.int32).share_memory_()
sl = slime(bno085_sd['abno085'], 1, exit_signal)
sensors = sl.sensors

delay_nanos = int(1_000_000_000/128)

while True:
    st = datetime.now()
    for sensor in sensors:
        sensor.read_data()


    if select.select([sys.stdin], [], [], 0)[0]:
        if sys.stdin.read(1) == 'q':
            print("got q going to start exiting")
            for sensor in sensors:
                sensor.write_exit_signal[0] = 1
            time.sleep(1)
            exit_signal[0] = 1
            break

    if (datetime.now() - st).microseconds * 1000 >  delay_nanos:
        print('loop skipped one ', (datetime.now() - st))
    nanos_to_delay = delay_nanos - (datetime.now().microsecond * 1000 % delay_nanos)
    time.sleep(delay_nanos/1_000_000_000)
print('exiting')

















