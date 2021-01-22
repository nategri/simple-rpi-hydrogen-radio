#!/bin/bash

for freq in 1420405752 1400000000; do
  for time in 300 120 60; do
    for gain in 300 500; do
      rtl_power_fftw -g $gain -f $freq -t $time -b 512 > hydrogen_baseline_g{$gain}_f{$freq}_t{$time}.dat
    done
  done
done
