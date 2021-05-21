import numpy as np
import pyvisa
import time
import binascii


class SDG1032X:
    def __init__(self, address='USB0::0xF4EC::0x1103::SDG1XCAQ4R2575::INSTR'):
        self.__address = address
        self.connect()

    def connect(self, address=None):
        rm = pyvisa.ResourceManager()
        if address is None:
            address = self.__address
        self.handle = rm.open_resource(address, timeout=20, chunk_size=1024000)

    def disconnect(self):
        self.handle.close()

    def output_on(self, channel=1):
        idx = self.__check_channel(channel, ['C1', 'C2'])
        self.handle.write(f"{channel}:OUTP ON")

    def output_off(self, channel=1):
        idx = self.__check_channel(channel, ['C1', 'C2'])
        self.handle.write(f"{channel}:OUTP OFF")

    def create_wave_file(
        self,
        fname,
        wave_points=[0x0010, 0x0020, 0x0030, 0x0040, 0x0050, 0x0060, 0x0070, 0xFF7F],
    ):
        """create a file"""
        def fix(b, l=6):
            s = ''
            for i in range(l-len(b)):
                s += '0'
            s +=  b
            return s

        b = [fix(hex(a)[2:]) for a in wave_points]
        with open(f"{fname}.bin", "wb") as f:
            for b_ in b:
                f.write(binascii.a2b_hex(b_))

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
        return options[channel - 1]

    def set_waveform(self, wavelist, channel=1):
        channel = self.__check_channel(channel, ["C1", "C2"])

        # if not fname.endswith(".bin"):
        #     fname += ".bin"

        # with open(fname, "rb") as f:
        #     data = f.read()
        data = self.__wavelist_to_bytes(wavelist)
        self.handle.write(
            f"{channel}:WVDT WVNM,wave1,FREQ,1.0,AMPL,2.0,OFST,0.0,PHASE,0.0,WAVEDATA,{data}",
            encoding='latin1'
        )
        self.handle.write("C1:ARWV NAME,wave1")

    def get_wave_data(self, fname):
        """get waveform from device"""
        data = self.handle.query("WVDT? user,wave1")
        findme = "WAVEDATA,b\'"
        data_pos = data.find(findme) + len(findme)
        data = data[data_pos:-3]
        # print(data)
        return self.__bytes_to_wavelist(data)

    def __wavelist_to_bytes(self, wavelist):
        def fix(b, l=4):
            s = ''
            for i in range(l-len(b)):
                s += '0'
            s +=  b
            s = s[2:4]+s[:2]
            return s

        b = [fix(hex(wave)[2:]) for wave in wavelist]
        bytestr = b''
        for b_ in b:
            bytestr += binascii.unhexlify(b_)
        return bytestr.decode('latin1')

    def __bytes_to_wavelist(self, bytestr):
        bytestr = bytestr.replace('\\', '').replace('x', '') #strip data return formatting
        wavelist = []
        for i in range(len(bytestr)//4):
            mask = slice(i*4, (i+1)*4)
            wavelist.append(int(bytestr[mask], 14))
        return wavelist