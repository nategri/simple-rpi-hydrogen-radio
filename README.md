<p align="center"><img src="/images/radio_telescope.gif"></p>
<p align="center"><i>A twenty hour drift scan of the Milky Way showing the 1420 MHz signature of hydrogen clouds.</i></p>

## Description

Example scripts for doing simple hydrogen line radio astronomy on the Raspberry Pi using inexpensive equipment
easily availble online. These do not comprise a good general-purpose "out of the box" solution, but should 
provide a useful template for those looking to do the same.

This approach is based on an excellent tutorial from the RTL-SDR Blog [1], but uses an inexpensive Raspberry Pi
for data acqusition instead of a Microsoft Windows PC. This allows for a more trivial external location and
continuous capture of the desktop to record results.

## Contents

* <i>take_baseline.sh</i> : Script for collecting baseline data (must be run before hydrogen_obvs.py, with 50 Ohm terminator attached
to LNA input instead of antenna)
* <i>hydrogen_obvs.py</i> : Script that collects power spectrum data and refreshes a plot
* <i>timelapse.sh</i> : Script to create timelapse of desktop (adjust per-second framerate and resolution with --framerate and -s options)

<p align="center"><img src="/images/radio_telescope.jpg"></p>
<p align="center"><i>Detailed view of hardware used for this experiment.</i></p>

## Rough Software Setup Guide

Acquire hardware as per Reference 1, selecting an SDR with a software-togglable bias-T, and an LNA powered via bias-T.

1. Install Raspbian on a Raspberry Pi, setup to be "headless" (also change default username/password)
2. Log in via ssh to Raspberry Pi and install xrdp to enable remote desktop logins
3. Log in to Rapsberry Pi via Microsoft Remote Desktop
4. Install rtl-sdr software as per Reference 2
5. Install rtl_power_fftw command line tool via Reference 3
6. Install Stellarium app, set to appropriate location/time, toggle alt-az coordinate grid and point toward zenith
7. Install matplotlib Python package
8. Connect 50 Ohm terminator to antenna input of LNA and acquire baseline data with <i>take_baseline.sh</i> script
9. Re-connect antenna and run <i>hydrogen_obvs.py</i> script to begin data acquisition and display
10. Run <i>timelapse.sh</i> to begin capturing a timelapse movie of desktop

## References

[1] https://www.rtl-sdr.com/a-good-quickstart-guide-for-rtl-sdr-linux-users/

[2] https://ranous.files.wordpress.com/2020/05/rtl-sdr4linux_quickstartguidev20.pdf

[3] https://github.com/AD-Vega/rtl-power-fftw
