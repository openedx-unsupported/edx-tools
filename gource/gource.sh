#!/bin/sh

gource \
    -s .015 \
    -1920x1080 \
    --auto-skip-seconds .25 \
    --multi-sampling \
    --stop-at-end \
    --key \
    --highlight-users \
    --hide mouse,progress \
    --file-idle-time 0 \
    --max-files 0  \
    --background-colour 000000 \
    --font-size 24 \
    --output-ppm-stream - \
    --output-framerate 30 \
    | avconv -y -r 30 -f image2pipe -vcodec ppm -i - -b 8192K movie.mp4
