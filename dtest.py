import copy
from icecream import ic
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

IPS = {'192.168.1.10': (0,'right-upper-arm'), '192.168.1.19': (1,'left-upper-arm')}

sensor_descriptors = {}
base_sds = bno085_sd["abno085"]['sensors']
for ip in IPS:
    for sd in base_sds:
        #change the name
        new_data_type = IPS[ip][1] + '-' + sd
        ic(new_data_type, IPS[ip][0])
        #also change the col_names
        new_col_names = []
        for cn in base_sds[sd]['col_names']:
            if cn.split('!')[0] == 'sampleDT':
                new_col_names.append(cn)
                continue
            new_col_names.append(IPS[ip][1] + '-' + cn)
        
        sensor_descriptors[new_data_type] =  copy.deepcopy(base_sds[sd])
        sensor_descriptors[new_data_type]['col_names'] = new_col_names
        #add a new field for this sensor
        sensor_descriptors[new_data_type]['buff_idx'] = IPS[ip][0]

ic(sensor_descriptors)