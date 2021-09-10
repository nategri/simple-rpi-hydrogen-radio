import os
import dateutil
import sys
import subprocess
import datetime
import json 
import numpy as np
import time

import usb

def parse_output(output):
    freqs = []
    dbs = []

    for line in output.split('\n'):

        try:
            f, d = [float(x) for x in line.split()[:2]]
        except:
            continue

        freqs.append(f)
        dbs.append(d)

    return freqs, dbs

if __name__ == '__main__':
    # Data acquisition commands (right from the rtl_power_fftw man page)
    SKY_COMMAND = 'rtl_power_fftw -d 1 -g 500 -f 1420405752 -r 2000000 -t 300 -b 512'
    BG_COMMAND = 'rtl_power_fftw -d 0 -g 500 -f 1420405752 -r 2000000 -t 300 -b 512'
    #SKY_COMMAND = '/home/nathan/rtl-power-fftw/build/rtl_power_fftw -d 0 -g 500 -f 1415000000 -r 2500000 -t 600 -b 512'
    #BG_COMMAND = '/home/nathan/rtl-power-fftw/build/rtl_power_fftw -d 1 -g 500 -f 1415000000 -r 2500000 -t 600 -b 512'

    #
    # Repeatedly collect and plot power data
    #
    print("Running data acquisition/plotting loop...")
    while True:
        time_string = datetime.datetime.utcnow().isoformat()
        sky_process = subprocess.Popen(
            SKY_COMMAND,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf8'
        )
        bg_process = subprocess.Popen(
            BG_COMMAND,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf8'
        )

        while True:
            try:
                sky_proc_out, _ = sky_process.communicate(timeout=600)
                bg_proc_out, _ = bg_process.communicate(timeout=600)
                break
            except subprocess.TimeoutExpired:
                print("Timeout! Resetting SDR hardware...")
                sky_process.kill()
                bg_process.kill()

                for usb_sdr in usb.core.find(idVendor=0x0bda, idProduct=0x2838, find_all=True):
                    usb_sdr.reset()

                time.sleep(5)

                sky_process = subprocess.Popen(
                    SKY_COMMAND,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf8'
                )
                bg_process = subprocess.Popen(
                    BG_COMMAND,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf8'
                )

            except:
                # Power cycle USB if all else fails
                subprocess.run('uhubctl -l 2 -a cycle')

        freqs, sky_dbs = parse_output(sky_proc_out)
        _, bg_dbs = parse_output(bg_proc_out)

        dbs = (np.array(sky_dbs) - np.array(bg_dbs)).tolist()

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

        print(datetime.datetime.utcnow())
