#!/bin/bash
LD_LIBRARY_PATH=/usr/local/lib rtl_biast -b 1
rtl_power_fftw -g 500 -f 1420405752 -t 300 -b 512 > hydrogen_baseline.dat
