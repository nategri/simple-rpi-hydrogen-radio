import os
import sys
import subprocess
import numpy as np
from matplotlib import pyplot

if __name__ == '__main__':
    # Command to enable bias-T to power LNA
    # (environment variable may not be needed in the future)
    ENABLE_BIAST_COMMAND = 'LD_LIBRARY_PATH=/usr/local/lib rtl_biast -b 1'

    # Data acquisition command (right from the man page)
    DATA_COMMAND = 'rtl_power_fftw -g 500 -f 1420405752 -B hydrogen_baseline.dat -t 300 -b 512'

    #
    # Enable bias-T
    #
    print("Enabling bias-T to power LNA")
    biast_process = subprocess.Popen(
        ENABLE_BIAST_COMMAND,
        shell=True
    )
    biast_process.wait()

    #
    # Inform that a baseline needs to be taken if file does not exist
    #
    if os.path.isfile('hydrogen_baseline.dat'):
        print("Baseline file found! Incorporating into output")
    else:
        print("Baseline file not found!")
        print("Connect 50 Ohm terminator to LNA input and collect baseline data by running take_baseline.sh")
        sys.exit()

    #
    # Repeatedly collect and plot power data
    #
    print("Running data acquisition/plotting loop...")
    while True:
        data_process = subprocess.Popen(
            DATA_COMMAND,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        power_proc_out, _ = data_process.communicate()

        freqs = []
        dbs = []
        for line in power_proc_out.split('\n'):

            try:
                f, d = [float(x) for x in line.split()[:2]]
            except:
                continue

            freqs.append(f)
            dbs.append(d)

        freqs = np.array(freqs) / 1.0e6

        pyplot.cla()
        pyplot.plot(freqs, dbs, '-b')
        pyplot.xlabel('MHz')
        pyplot.ylabel('dB / Hz')
        #pyplot.ylim(-67, -62)
        pyplot.xticks(fontsize=8)
        pyplot.yticks(fontsize=8)
        pyplot.pause(0.5)
        pyplot.draw()
