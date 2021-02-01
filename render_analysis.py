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
            d = data['decibels']
            dt = dateutil.parser.parse(data['timestamp'])

            f_lower = f[0] + 2.0e5
            f_upper = f[-1] - 2.0e5

            f_trimmed = []
            d_trimmed = []
            for f, d in zip(f, d):
                if (f > f_lower) and (f < f_upper):
                    f_trimmed.append(f)
                    d_trimmed.append(d)

            power_unitless = power_unitless_trimmed = [np.power(10.0,  x/10.0) for x in d_trimmed]
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
        

    def render(self, filename, azel, image):
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
        self._ax[0][1].clear()
        self._ax[1][0].clear()
        self._ax[1][1].clear()

        self._fig.suptitle(current_date_string[:-5])

        # Spectrum plot
        freqs = current_freq_data['frequency']
        dbs = current_freq_data['decibels']
        dbs_median = np.median(current_freq_data['decibels'])
        self._ax[0][0].plot(np.array(freqs) / 1.0e6, dbs, '-b', label='Spectrum')
        self._ax[0][0].set_ylim(dbs_median - 0.2, dbs_median + 1.5)
        self._ax[0][0].set_xlabel('MHz')
        self._ax[0][0].set_ylabel('dB / Hz')
        self._ax[0][0].tick_params(labelsize=8)
        self._ax[0][0].set_xlim(bottom_freq, top_freq)
        self._ax[0][0].legend(loc='upper left')

        # Waterfall plot
        waterfall_data = [x['decibels'] for x in freq_data][::-1]
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
        self._ax[1][0].imshow(waterfall_data, extent=[bottom_freq, top_freq, 0.0, 1.0], cmap='jet', aspect='auto', vmin=-6.6, vmax=-5.5)

        # Map plot
        # Credit to: https://github.com/0xCoto/Virgo
        ra, dec = self._azel_to_radec(azimuth, elevation, current_date_string)
        self._ax[0][1].imshow(self._sky_data, extent=[24, 0, -90, 90], aspect='auto', interpolation='gaussian')
        self._ax[0][1].set_xlabel('Right Ascension')
        self._ax[0][1].set_ylabel('Declination')
        self._ax[0][1].tick_params(labelsize=8)
        self._ax[0][1].scatter(ra, dec, s=200, color=[0.85, 0.15, 0.16], label='Telescope')
        self._ax[0][1].legend(loc='upper left')

        # Power plot
        self._ax[1][1].plot(power_data[0], power_data[1], 'ob', markersize=2.5, label='Average Power')
        self._ax[1][1].set_xlabel('Previous 12 Hours')
        self._ax[1][1].set_ylabel('dB')
        self._ax[1][1].set_xlim(power_data[0][-1] - datetime.timedelta(days=0.5), power_data[0][-1])
        self._ax[1][1].set_ylim(-6.5, -6.2)
        self._ax[1][1].tick_params(labelsize=8)
        for tick_label in self._ax[1][1].get_xticklabels():
            tick_label.set_ha("right")
            tick_label.set_rotation(30)
        self._ax[1][1].legend(loc='upper left')


        # Wrap up
        pyplot.tight_layout()
        pyplot.savefig(image+'.png')

if __name__ == "__main__":
    TIMESTEP = 5 # Minutes
    DAY_OF_TIMESTEPS = int((24*60/TIMESTEP))

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

    fileames = sorted(os.listdir(args.data))

    for i, fn in enumerate(fileames):
        print("{} of {}".format(i, len(fileames)))
        data_renderer.render(fn, (args.az, args.el), image='render_output/'+str(i).zfill(4))
