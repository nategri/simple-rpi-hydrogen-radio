#!/bin/bash

ffmpeg -framerate 0.05 -f x11grab -s 1400,1050 -i :10.0+0,0 -vf settb=\(1/30\),setpts=N/TB/30 -r 30 -vcodec libx264 -crf 0 -preset ultrafast -threads 0 video_output1.mkv
