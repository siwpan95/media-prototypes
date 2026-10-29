#!/bin/bash
set -e
cd "$(dirname "$0")"
# 输出随仓库走（原硬编码 WorkBuddy 旧路径，2026-08-28 修复）
ffmpeg -y -i segments/raw_video.mp4 -i audio/full_audio.m4a -vf "subtitles=subtitles/full.srt:force_style='FontName=Microsoft YaHei,FontSize=40,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=3,Shadow=0,Alignment=2,MarginV=70,BorderStyle=1'" -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 23 -c:a copy -shortest "火车进站_10分钟.mp4"
