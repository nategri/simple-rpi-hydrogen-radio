import argparse
import datetime
import scipy
from matplotlib import pyplot
import numpy as np
import os
import json
import dateutil

from astropy.time import Time as AstroTime
from astropy.coordinates import SkyCoord as AstroSkyCoord
from astropy.coordinates import EarthLocation as AstroEarthLocation
from astropy.coordinates import AltAz as AstroAltAz
import astropy.units as AstroUnits

import sys
import multiprocessing as mp

WATERFALL_PLOT_MIN = -4.1
WATERFALL_PLOT_MAX = -3.5

POWER_PLOT_MIN = -4.1
POWER_PLOT_MAX = -3.9

class TelescopeData:
    def __init__(self, directory):
        self._data = []

        for fn in os.listdir(directory):
            full_fn = '/'.join([directory, fn])
            with open(full_fn, 'r') as file:
                file_data = json.loads(file.read())
                file_data['filename'] = fn
                self._data.append(file_data)

        self._data = sorted(self._data, key=lambda x: x['timestamp'])

    def power(self, data_list, agg_func=np.average):

        t_list = []
        p_list = []

        for data in data_list:
            f = data['frequency']
            d = -1*np.array(data['decibels']) # Multiply by -1 if background and signal are swapped in data files
            dt = dateutil.parser.parse(data['timestamp'])

            f_lower = f[0] + 2.0e5
            f_upper = f[-1] - 2.0e5

            f_trimmed = [x for x, y in zip(f, d) if x > f_lower and x < f_upper]
            d_trimmed = [y for x, y in zip(f, d) if x > f_lower and x < f_upper]

            power_unitless_trimmed = [np.power(10.0,  x/10.0) for x in d_trimmed]
            power_unitless_agg = agg_func(power_unitless_trimmed)

            p = 10 * np.log10(power_unitless_agg)

            t_list.append(dt)
            p_list.append(p)

        return t_list, p_list

    def spectrum(self):
        return self._data

    # Returns power and spectrum data up until and including filename
    def get_data_for_filename(self, filename):
        data_subset = [x for x in self._data if x['filename'] <= filename]

        return data_subset, (self.power(data_subset))

class DataRenderer:
    def __init__(self, data_directory):
        self._telescope_data = TelescopeData(data_directory)
        self._fig, self._ax = pyplot.subplots(nrows=2, ncols=2, figsize=(16, 8))
        self._sky_data = np.loadtxt('neutral_hydrogen_sky.dat')
        self._sky_data = np.flip(self._sky_data, 1)

        self._ax[0][1].imshow(self._sky_data, extent=[24, 0, -90, 90], aspect='auto', interpolation='gaussian')
        self._telescope_position_scatter = None

    def _azel_to_radec(self, az, el, date_string):
        # Credit to: https://github.com/0xCoto/Virgo

        try:
            lat = float(os.environ['RADIO_TELESCOPE_LATITUDE'])
            lon = float(os.environ['RADIO_TELESCOPE_LONGITUDE'])
            alt = float(os.environ['RADIO_TELESCOPE_ALTITUDE'])
        except KeyError:
            print("Please set RADIO_TELESCOPE_[LATITUDE, LONGITUDE, ALTITUDE] environment variables")
            sys.exit(1)

        earth_location = AstroEarthLocation(lat=lat*AstroUnits.deg, lon=lon*AstroUnits.deg, height=alt*AstroUnits.m)
        astro_time = AstroTime(date_string+'Z', format='isot', scale='utc')
        sky_coord = AstroSkyCoord(
            alt=el*AstroUnits.deg,
            az=az*AstroUnits.deg,
            obstime=astro_time,
            frame='altaz',
            location=earth_location
        )

        icrs_coord = sky_coord.icrs

        return icrs_coord.ra.hour, icrs_coord.dec.deg
        

    def render(self, filename, azel):
        TIMESTEP = 5 # Minutes
        DAY_OF_TIMESTEPS = int((24*60/TIMESTEP))

        azimuth, elevation = azel

        # Retrieve data
        freq_data, power_data = self._telescope_data.get_data_for_filename(filename)
        current_freq_data = freq_data[-1]
        current_date_string = freq_data[-1]['timestamp']
        print(current_date_string)
        bottom_freq = current_freq_data['frequency'][0] / 1.0e6
        top_freq = current_freq_data['frequency'][-1] / 1.0e6

        # Clear plot
        self._ax[0][0].clear()
        #self._ax[0][1].clear()
        self._ax[1][0].clear()
        self._ax[1][1].clear()

        if self._telescope_position_scatter is not None:
            self._telescope_position_scatter.remove()

        self._fig.suptitle(current_date_string[:-5])

        # Spectrum plot
        freqs = current_freq_data['frequency']
        dbs = -1*np.array(current_freq_data['decibels'])
        dbs_median = np.median(dbs)
        self._ax[0][0].plot(np.array(freqs) / 1.0e6, dbs, '-b', label='Spectrum')
        self._ax[0][0].set_ylim(dbs_median - 0.2, dbs_median + 1.5)
        self._ax[0][0].set_xlabel('MHz')
        self._ax[0][0].set_ylabel('dB / Hz')
        self._ax[0][0].tick_params(labelsize=8)
        self._ax[0][0].set_xlim(bottom_freq, top_freq)
        self._ax[0][0].legend(loc='upper left')

        # Waterfall plot
        waterfall_data = [-1*np.array(x['decibels']) for x in freq_data][::-1]
        if len(waterfall_data) < DAY_OF_TIMESTEPS:
            diff = DAY_OF_TIMESTEPS - len(waterfall_data)
            pad = [len(waterfall_data[0])*[-10.0] for _ in range(diff)]
            waterfall_data += pad
        elif len(waterfall_data) > DAY_OF_TIMESTEPS:
            waterfall_data = waterfall_data[:DAY_OF_TIMESTEPS]
        self._ax[1][0].set_xlabel('MHz')
        self._ax[1][0].get_yaxis().set_ticks([])
        self._ax[1][0].set_ylabel('Previous 24 Hours')
        self._ax[1][0].tick_params(labelsize=8)
        self._ax[1][0].imshow(
            waterfall_data,
            extent=[
                bottom_freq,
                top_freq,
                0.0,
                1.0
            ],
            cmap='jet',
            aspect='auto',
            vmin=WATERFALL_PLOT_MIN,
            vmax=WATERFALL_PLOT_MAX
        )

        # Map plot
        # Credit to: https://github.com/0xCoto/Virgo
        ra, dec = self._azel_to_radec(azimuth, elevation, current_date_string)
        self._ax[0][1].set_xlabel('Right Ascension')
        self._ax[0][1].set_ylabel('Declination')
        self._ax[0][1].tick_params(labelsize=8)
        self._telescope_position_scatter = self._ax[0][1].scatter(ra, dec, s=200, color=[0.85, 0.15, 0.16], label='Telescope')
        self._ax[0][1].legend(loc='upper left')

        # Power plot
        self._ax[1][1].plot(power_data[0], power_data[1], 'ob', markersize=2.5, label='Average Power')
        self._ax[1][1].set_xlabel('Previous 12 Hours')
        self._ax[1][1].set_ylabel('dB')
        self._ax[1][1].set_xlim(power_data[0][-1] - datetime.timedelta(days=0.5), power_data[0][-1])
        self._ax[1][1].set_ylim(POWER_PLOT_MIN, POWER_PLOT_MAX)
        self._ax[1][1].tick_params(labelsize=8)
        for tick_label in self._ax[1][1].get_xticklabels():
            tick_label.set_ha("right")
            tick_label.set_rotation(30)
        self._ax[1][1].legend(loc='upper left')


        # Wrap up
        pyplot.tight_layout()
        pyplot.savefig('./render_output/'+filename.split('.')[0]+'.png')

def mp_proc_func(dr, filename, args):
    print(filename)
    dr.render(filename, (args.az, args.el))

if __name__ == "__main__":

    num_processed = 0

    parser = argparse.ArgumentParser(
        description="Render available data radio telescope data into a movie."
    )
    parser.add_argument(
        '--data',
        metavar='DIR',
        type=str,
        nargs='?',
        required=True,
        help='Data directory'
    )
    parser.add_argument(
        '--az',
        metavar='DEG',
        type=float,
        nargs='?',
        required=True,
        help='Azimuth of telescope'
    )
    parser.add_argument(
        '--el',
        metavar='DEG',
        type=float,
        nargs='?',
        required=True,
        help='Elevation of telescope'
    )
    args = parser.parse_args()
    
    data_renderer = DataRenderer(args.data)

    filenames = sorted(os.listdir(args.data))[int(-1.5*288):]

    pool = mp.Pool(4)
    for fn in filenames:
        pool.apply_async(mp_proc_func, args=(data_renderer, fn, args))
    pool.close()
    pool.join()
