# Hikvison-NVR-Capture
海康威视NVR批量截图巡检留存
食用方法：
提前下载ffmpeg.exe以及准备一份nvr_list.txt 存放海康NVR的IP地址，每行放一个IP地址，将两者放入py脚本同文件夹内然后运行。

# Hikvision NVR Batch Snapshot Tool

A professional Python tool for batch capturing snapshots from Hikvision IP cameras via RTSP using FFmpeg.

本项目用于海康威视 NVR 摄像机批量截图，自动判断通道数量，通过 RTSP 调用 FFmpeg 实现自动抓图，适用于监控巡检与离线排查。

---

## 🚀 Features

- Batch snapshot from multiple IPC cameras
- RTSP stream capture
- FFmpeg based grabbing
- Timeout control
- Automatic image saving
- Simple configuration

---

## 🏗 Supported Devices

- Hikvision NVR

(Other brands see related repositories)

---

## 🧰 Tech Stack

- Python 3.x
- FFmpeg
- RTSP protocol

---


```bash
pip install -r requirements.txt
