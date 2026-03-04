import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区域 =================
NVR_LIST_FILE = "HikvisionNVR.txt"  # 每行一个 NVR IP
USERNAME = "admin"
PASSWORD = "NVR密码"
SAVE_ROOT = "nvr_snapshots"
FFMPEG_PATH = "ffmpeg"
TIMEOUT_API = 5
TIMEOUT_FFMPEG = 30
MAX_NVR_THREADS = 5  # 同时对多少台 NVR 发起 API 请求
# ===========================================

os.makedirs(SAVE_ROOT, exist_ok=True)


def get_nvr_channels(nvr_ip):
    """通过 API 获取单台 NVR 的所有有效通道信息"""
    url = f"http://{nvr_ip}/ISAPI/ContentMgmt/InputProxy/channels"
    tasks = []
    try:
        r = requests.get(url, auth=HTTPDigestAuth(USERNAME, PASSWORD), timeout=TIMEOUT_API)
        if r.status_code != 200:
            print(f" [!] {nvr_ip} 登录失败或 API 不支持 (Status: {r.status_code})")
            return []

        # 处理命名空间
        root = ET.fromstring(r.text)
        ns = {'h': 'http://www.hikvision.com/ver20/XMLSchema'}

        channels = root.findall('.//h:InputProxyChannel', ns)
        for ch in channels:
            ch_id = ch.find('h:id', ns).text
            ch_name = ch.find('h:name', ns).text
            # 过滤掉非法文件名字符
            safe_name = "".join([c for c in ch_name if c.isalnum() or c in (' ', '_')]).strip()

            tasks.append({
                "nvr_ip": nvr_ip,
                "ch_id": ch_id,
                "ch_name": safe_name
            })
        print(f" [√] {nvr_ip} 成功发现 {len(tasks)} 个通道")
    except Exception as e:
        print(f" [×] {nvr_ip} 获取通道异常: {e}")
    return tasks


def take_snapshot(task):
    """执行 FFmpeg 截图"""
    nvr_ip = task['nvr_ip']
    ch_id = task['ch_id']
    ch_name = task['ch_name']

    # 建立目录结构：snapshots/NVR_IP/通道名.jpg
    nvr_dir = os.path.join(SAVE_ROOT, nvr_ip)
    os.makedirs(nvr_dir, exist_ok=True)

    # 海康 NVR RTSP 规则：ID + 01
    rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{nvr_ip}/Streaming/Channels/{ch_id}01"
    output_path = os.path.join(nvr_dir, f"CH{ch_id}_{ch_name}.jpg")

    cmd = [
        FFMPEG_PATH,
        "-rtsp_transport", "tcp",
        "-y",
        "-i", rtsp_url,
        "-frames:v", "1",
        "-q:v", "2",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=TIMEOUT_FFMPEG)
        if os.path.exists(output_path):
            return True, f"{nvr_ip} CH{ch_id} OK"
    except:
        pass
    return False, f"{nvr_ip} CH{ch_id} Fail"


def main():
    # 1. 加载 NVR IP 列表
    if not os.path.exists(NVR_LIST_FILE):
        print(f"找不到 {NVR_LIST_FILE}")
        return
    with open(NVR_LIST_FILE, "r") as f:
        nvr_ips = [line.strip() for line in f if line.strip()]

    # 2. 批量获取所有 NVR 的通道任务 (使用多线程)
    print(f"正在读取 {len(nvr_ips)} 台 NVR 的通道信息...")
    all_tasks = []
    with ThreadPoolExecutor(max_workers=MAX_NVR_THREADS) as executor:
        results = executor.map(get_nvr_channels, nvr_ips)
        for res in results:
            all_tasks.extend(res)

    print(f"\n任务汇总完毕，共计 {len(all_tasks)} 个通道待截图。")
    print("开始截图（建议顺序执行以保护 NVR 性能）...\n")

    # 3. 执行截图
    # 注意：这里如果也用高并发，可能会把 45 台 NVR 的上行带宽占满或者让 NVR 拒绝服务
    # 建议使用较小的并发，或者干脆顺序执行
    success_count = 0
    for i, task in enumerate(all_tasks):
        success, msg = take_snapshot(task)
        if success:
            success_count += 1
            print(f"[{i + 1}/{len(all_tasks)}] [√] {msg}")
        else:
            print(f"[{i + 1}/{len(all_tasks)}] [×] {msg}")

    print(f"\n全部完成！成功: {success_count}, 失败: {len(all_tasks) - success_count}")


if __name__ == "__main__":

    main()
