import torch
import numpy as np
from datetime import datetime, timedelta, timezone
import sys


# make num buffers dynamic
# is there a way to make them work by insertion and not time?
# when the writer goes to read they'll only know the current time
# the writer could always check if the datetime is greater than the last one it wrote
# and still check every second, a bit of a workaround but eh

# let's use 5 1 second buffers to be safe and make sure we're not losing anything
class CircularTimeSeriesBuffers:
    def __init__(self, hz, DTYPE, length=1, numBuffs = 5):
        # shape is a tuple where
        #   first dimenstion is the number of samples per buffer
        #   subsequent dimensions are the shape the data
        #print("initializing")
        self.numBuffs = torch.zeros(1, dtype=torch.int32).share_memory_()
        self.numBuffs[0] = numBuffs
        self.size = torch.zeros(1, dtype=torch.int32).share_memory_()
        self.size[0] = hz 
        self.lastbn = torch.zeros(1, dtype=torch.int32).share_memory_()
        self.bn = torch.zeros(1, dtype=torch.int32).share_memory_()

        # Shared memory buffers
        self.nextidxs = torch.zeros((numBuffs,1), dtype=torch.int32).share_memory_()  # Most recent index (insertion point)
        self.lengths = torch.zeros((numBuffs,1), dtype=torch.int32).share_memory_()
        self.data_buffers = torch.zeros((numBuffs, hz, length), dtype=DTYPE).share_memory_()
        self.time_buffers = torch.zeros((numBuffs, self.size[0]), dtype=torch.int64).share_memory_()
        #print("initialized")
        #sys.stdout.flush()

    def bufferNum(self, timestamp):
        return timestamp.second % self.numBuffs
    
    def __setitem__(self, index, value):
        """Set value and timestamp at a circular index."""
        #print("in set item")
        #sys.stdout.flush()
        index = index % self.size[0]  # Ensure circular indexing
        self.data_buffers[self.bn[0]][index] = torch.tensor(value[0])  # Assume value is a tuple (data, timestamp)
        self.time_buffers[self.bn[0]][index] = torch.tensor(int(value[1].replace(tzinfo=timezone.utc).timestamp() * 1e9))
            
    def __getitem__(self, index):
        """Retrieve (value, timestamp) from a circular index."""
        index = index % self.size[0]  # Ensure circular indexing
        ts_ns = self.time_buffer[index].item()  # Get timestamp in ns
        timestamp = datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc)  # Convert back to datetime
        return self.data_buffer[index], timestamp

    def append(self, value, timestamp):
        """Append a new data point with a timezone-aware timestamp (microsecond precision)."""
        #print("in append")
        #sys.stdout.flush()
        # get the current buffer number to use, and reset the old one if we switched
        self.lastbn[0] = self.bn[0].clone()
        self.bn[0] = self.bufferNum(timestamp)
        if self.bn[0] != self.lastbn[0]:
            self.nextidxs[self.lastbn[0]][0] = 0
            self.lengths[self.bn[0]][0] = 0
        
        self[self.nextidxs[self.bn[0]][0]] = (value, timestamp)  # Use __setitem__
        
        #print(f"self.nextidx before incrementing {self.nextidx[0]}")
        self.nextidxs[self.bn[0]][0] = self.nextidxs[self.bn[0]][0] + 1  # Move to next index
        self.lengths[self.bn[0]][0] = self.lengths[self.bn[0]][0] + 1
        #print(f"self.nextidx after incrementing {self.nextidx[0]}")
