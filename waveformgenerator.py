import numpy as np
import visa
import time
import binascii


class SDG1032X:
    def __init__(self, address):
        self.__address = address
        self.connect()

    def connect(self, address=None):
        if address is None:
            address = self.__address
        self.handle = visa.instrument(address, timeout=20, chunk_size=1024000)

    def disconnect(self):
        self.handle.close()

    def output_on(self, channel=1):
        channel = __check_channel(channel, [153, 152])
        self.handle.write(f"VKEY VALUE,{buttonidx},STATE,1")

    def output_on(self, channel=1):
        channel = __check_channel(channel, [153, 152])
        self.handle.write(f"VKEY VALUE,{buttonidx},STATE,0")

    def create_wave_file(
        self,
        fname,
        wave_points=[0x0010, 0x0020, 0x0030, 0x0040, 0x0050, 0x0060, 0x0070, 0xFF7F],
    ):
        """create a file"""
        f = open(f"{fname}.bin", "wb")

        b = [hex(a) for a in wave_points]
        b = b[2:]
        len_b = len(b)

        if 0 == len_b:
            b = "0000"
        elif 1 == len_b:
            b = "000" + b
        elif 2 == len_b:
            b = "00" + b
        elif 3 == len_b:
            b = "0" + b
        c = binascii.a2b_hex(b)  # Hexadecimal integer to ASCii encoded string
        f.write(c)
        f.close()

    def __check_channel(self, channel: int, options=[1, 2]):
        """confirms that a valid channel number was provided. If yes, returns the relevant option for that channel

        Args:
            channel (int): channel number (1 or 2)
            options (list, optional): two outputs corresponding to channel 1 and 2. Defaults to [1,2].

        Raises:
            ValueError: If a channel number other than 1 or 2 is provided, cannot proceed

        Returns:
            value corresponding to the channel number
        """
        if channel not in [1, 2]:
            raise ValueError("Channel must be 1 or 2!")
        return channel[channel - 1]

    def send_wave_data(self, fname, channel=1):
        channel = __check_channel(channel, ["C1", "C2"])

        if not fname.endswith(".bin"):
            fname += ".bin"

        with open(fname, "rb") as f:
            data = f.read()
        self.handle.write(
            f"{channel}:WVDT WVNM,wave1,FREQ,2000.0,AMPL,1.0,OFST,0.0,PHASE,0.0,WAVEDATA,{data:s}"
        )
        self.handle.write("C1:ARWV NAME,wave1")

    def get_wave_data(self, fname):
        """get waveform from device"""
        with open(f"{fname}.bin", "wb") as f:
            self.handle.write("WVDT? user,wave1")
            time.sleep(1)
            data = self.handle.read()
            findme = "WAVEDATA,"
            data_pos = data.find(findme) + len(findme)
            data = data[data_pos:]
            f.write(data)
