#!/bin/bash

for time in 300 120 60; do
  for gain in 300 500; do
    rtl_power_fftw -g $gain -f 1420405752 -t $time -b 512 > hydrogen_baseline_g{$gain}_t{$time}.dat
  done
done
