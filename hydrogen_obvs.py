import os
import dateutil
import sys
import subprocess
import datetime
import json 
import numpy as np
from matplotlib import pyplot

def retrieve_power_data():
    data_dir = './data'
    data_filenames = sorted(os.listdir(data_dir))

    avg_p = []
    t = []

    for i, filename in enumerate(data_filenames):
        with open('/'.join([data_dir, filename]), 'r') as f:
            data = json.loads(f.read())

        f = data['frequency']
        d = data['decibels']
        dt = dateutil.parser.parse(data['timestamp'])

        f_trimmed = []
        d_trimmed = []
        for f, d in zip(f, d):
            if (f > 1419.75e6) and (f<1421.25e6):
                f_trimmed.append(f)
                d_trimmed.append(d)

        power_unitless = power_unitless_trimmed = [np.power(10.0,  x/10.0) for x in d_trimmed]
        power_unitless_average = np.average(power_unitless_trimmed)
        power_unitless_median = np.median (power_unitless_trimmed)

        db_average = 10 * np.log10(power_unitless_average)
        db_median = 10 * np.log10(power_unitless_median)

        y = db_average
        x = dt

        avg_p.append(y)
        t.append(dt)

    return t, avg_p

if __name__ == '__main__':
    # Command to enable bias-T to power LNA
    # (environment variable may not be needed in the future)
    ENABLE_BIAST_COMMAND = 'LD_LIBRARY_PATH=/usr/local/lib rtl_biast -b 1'

    # Data acquisition command (right from the man page)
    DATA_COMMAND = 'rtl_power_fftw -g 500 -f 1420405752 -B hydrogen_baseline_g500_f1420405752_t300.dat -t 300 -b 512'

    #
    # Enable bias-T
    #
    """
    print("Enabling bias-T to power LNA")
    biast_process = subprocess.Popen(
        ENABLE_BIAST_COMMAND,
        shell=True
    )
    biast_process.wait()
    """

    #
    # Inform that a baseline needs to be taken if file does not exist
    #
    if os.path.isfile('hydrogen_baseline.dat'):
        print("Baseline file found! Incorporating into output")
    else:
        print("Baseline file not found!")
        print("Connect 50 Ohm terminator to LNA input and collect baseline data by running take_baseline.sh")
        sys.exit()

    fig, ax = pyplot.subplots(2, figsize=(8, 8))

    #
    # Repeatedly collect and plot power data
    #
    print("Running data acquisition/plotting loop...")
    while True:
        time_string = datetime.datetime.utcnow().isoformat()
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

        # Save data file
        filename = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
        assert len(freqs) == len(dbs)
        with open('./data/telescope_data_'+filename+'.json', 'w') as f:
            data = {
                'timestamp': time_string,
                'frequency': freqs,
                'decibels': dbs
            }

            f.write(json.dumps(data))

        freqs = np.array(freqs) / 1.0e6

        dbs_std = np.std(dbs)
        dbs_median = np.median(dbs)

        x_pow, y_pow = retrieve_power_data()

        ax[0].clear()
        ax[1].clear()

        ax[0].plot(freqs, dbs, '-b')
        ax[0].set_ylim(dbs_median - 0.2, dbs_median + 1.5)
        ax[0].set_xlabel('MHz')
        ax[0].set_ylabel('dB / Hz')
        ax[0].tick_params(labelsize=8)

        ax[1].plot(x_pow, y_pow, '*b')
        ax[1].set_xlabel('Date')
        ax[1].set_ylabel('Power')
        for tick_label in ax[1].get_xticklabels():
            tick_label.set_ha("right")
            tick_label.set_rotation(30)

        pyplot.tight_layout()

        pyplot.pause(0.5)
        pyplot.draw()

        print(datetime.datetime.utcnow())
