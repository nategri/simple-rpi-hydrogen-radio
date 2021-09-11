#!/bin/bash
rsync -aP nathan@radio-telescope.local:/home/nathan/simple-rpi-hydrogen-radio/data/ telescope_data_2021_09_09
python3 render_analysis.py --az 180 --el 16 --data telescope_data_2021_09_09/ && \
#ffmpeg -y -r 15 -f image2 -i render_output/%04d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p data_movie.mp4
ffmpeg -y -r 15 -pattern_type glob -i 'render_output/*.png' -pix_fmt yuv420p -c:v libx264 out.mp4
