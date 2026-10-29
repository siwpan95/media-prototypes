#!/bin/bash
set -e
cd "$(dirname "$0")"
ffmpeg -y -i scene_01.mp3 -af "apad=whole_dur=30" -c:a aac -ar 48000 -b:a 192k scene_01_pad.m4a
ffmpeg -y -i scene_02.mp3 -af "apad=whole_dur=40" -c:a aac -ar 48000 -b:a 192k scene_02_pad.m4a
ffmpeg -y -i scene_03.mp3 -af "apad=whole_dur=70" -c:a aac -ar 48000 -b:a 192k scene_03_pad.m4a
ffmpeg -y -i scene_04.mp3 -af "apad=whole_dur=55" -c:a aac -ar 48000 -b:a 192k scene_04_pad.m4a
ffmpeg -y -i scene_05.mp3 -af "apad=whole_dur=55" -c:a aac -ar 48000 -b:a 192k scene_05_pad.m4a
ffmpeg -y -i scene_06.mp3 -af "apad=whole_dur=60" -c:a aac -ar 48000 -b:a 192k scene_06_pad.m4a
ffmpeg -y -i scene_07.mp3 -af "apad=whole_dur=50" -c:a aac -ar 48000 -b:a 192k scene_07_pad.m4a
ffmpeg -y -i scene_08.mp3 -af "apad=whole_dur=50" -c:a aac -ar 48000 -b:a 192k scene_08_pad.m4a
ffmpeg -y -i scene_09.mp3 -af "apad=whole_dur=55" -c:a aac -ar 48000 -b:a 192k scene_09_pad.m4a
ffmpeg -y -i scene_10.mp3 -af "apad=whole_dur=50" -c:a aac -ar 48000 -b:a 192k scene_10_pad.m4a
ffmpeg -y -i scene_11.mp3 -af "apad=whole_dur=45" -c:a aac -ar 48000 -b:a 192k scene_11_pad.m4a
ffmpeg -y -i scene_12.mp3 -af "apad=whole_dur=50" -c:a aac -ar 48000 -b:a 192k scene_12_pad.m4a
ffmpeg -y -f concat -safe 0 -i concat.txt -af "apad=whole_dur=610" -c:a aac -ar 48000 -b:a 192k full_audio.m4a
