"""
Download data from a Rigol DS1052E oscilloscope and graph with matplotlib.
By Ken Shirriff, http://righto.com/rigol

Based on http://www.cibomahto.com/2010/04/controlling-a-rigol-oscilloscope-using-linux-and-python/
by Cibo Mahto.
"""

import numpy as np
import visa

# Get the USB device, e.g. 'USB0::0x1AB1::0x0588::DS1ED141904883'
# instruments = visa.get_instruments_list()
# usb = filter(lambda x: 'USB' in x, instruments)
# if len(usb) != 1:
#     print 'Bad instrument list', instruments
#     sys.exit(-1)
# scope = visa.instrument(usb[0], timeout=20, chunk_size=1024000) # bigger timeout for long mem


class RigolDS1102E:
    def __init__(self, address):
        self.__address = address
        self.connect()

    def connect(self, address=None):
        if address is None:
            address = self.__address
        self.handle = visa.instrument(address, timeout=20, chunk_size=1024000)

    def disconnect(self):
        self.handle.close()

    def read(self, channel=1):
        if channel not in [1, 2]:
            raise ValueError("Channel must be 1 or 2.")

        self.handle.write(":STOP")  # stop acquisiton
        timescale = self.handle.ask_for_values(":TIM:SCAL?")[0]
        timeoffset = self.handle.ask_for_values(":TIM:OFFS?")[0]
        voltscale = self.handle.ask_for_values(":CHAN1:SCAL?")[0]
        voltoffset = self.handle.ask_for_values(":CHAN1:OFFS?")[0]
        self.handle.write(":WAV:POIN:MODE RAW")
        rawdata = self.handle.ask(":WAV:DATA? CHAN1")[10:]
        data_size = len(rawdata)
        sample_rate = self.handle.ask_for_values(":ACQ:SAMP?")[0]
        self.scope.write(":KEY:FORCE")
        data = np.frombuffer(rawdata, "B")

        # Walk through the data, and map it to actual voltages
        # This mapping is from Cibo Mahto
        # First invert the data
        data = data * -1 + 255

        # Now, we know from experimentation that the scope display range is actually
        # 30-229.  So shift by 130 - the voltage offset in counts, then scale to
        # get the actual voltage.
        data = (data - 130.0 - voltoffset / voltscale * 25) / 25 * voltscale

        # Now, generate a time axis.
        time = np.linspace(
            timeoffset - 6 * timescale, timeoffset + 6 * timescale, num=len(data)
        )

        # # See if we should use a different time axis
        # if time[-1] < 1e-3:
        #     time = time * 1e6
        #     tUnit = "uS"
        # elif time[-1] < 1:
        #     time = time * 1e3
        #     tUnit = "mS"
        # else:
        #     tUnit = "S"
        return time, data
