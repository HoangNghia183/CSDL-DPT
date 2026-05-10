import os
import requests
import time
import re

# --- CẤU HÌNH THÔNG SỐ ---
API_KEY = "V8joi3VX3FGN5BBEEOJJTxV7rheTagMozGHJ3SLWvcIGAKDReQ42RYsp" 
QUERY_TERMS = [
    "flowers",
    "flower",
    "floral",
    "blossom",
    "bloom",
    "bouquet",
    "garden flowers",
    "wildflowers",
    "rose",
    "tulip",
]
TOTAL_VIDEOS_NEEDED = 550
VIDEOS_PER_PAGE = 80 # Pexels cho tối đa 80 kết quả/trang
OUTPUT_FOLDER = "pexels_dataset"
MAX_RETRIES = 4
SEARCH_TIMEOUT = 25
DOWNLOAD_TIMEOUT = 60
BACKOFF_SECONDS = 2
MAX_PAGES_PER_TERM = 30

# --- KHỞI TẠO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, OUTPUT_FOLDER)
os.makedirs(OUTPUT_DIR, exist_ok=True)

headers = {
    "Authorization": API_KEY
}

downloaded_count = 0
seen_ids = set()


def extract_video_id(file_name):
    match = re.search(r"_(\d+)\.mp4$", file_name)
    if match:
        return int(match.group(1))
    return None


for file_name in os.listdir(OUTPUT_DIR):
    if file_name.startswith("vid_") and file_name.endswith(".mp4"):
        existing_id = extract_video_id(file_name)
        if existing_id is not None:
            seen_ids.add(existing_id)

downloaded_count = len(seen_ids)


def request_with_retry(url, headers=None, stream=False, timeout=30, max_retries=3):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, stream=stream, timeout=timeout)
            if response.status_code >= 500:
                raise requests.HTTPError(f"Server error {response.status_code}")
            return response
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as err:
            last_error = err
            if attempt < max_retries:
                wait_time = BACKOFF_SECONDS * attempt
                print(f"  -> Lần {attempt}/{max_retries} thất bại, thử lại sau {wait_time}s...")
                time.sleep(wait_time)

    raise last_error

print(
    f"Bắt đầu tải {TOTAL_VIDEOS_NEEDED} video với các chủ đề: {', '.join(QUERY_TERMS)}..."
)
if downloaded_count > 0:
    print(f"Đã có sẵn {downloaded_count} video, sẽ tiếp tục tải phần còn thiếu...")

# --- VÒNG LẶP LẤY DỮ LIỆU ---
for query in QUERY_TERMS:
    if downloaded_count >= TOTAL_VIDEOS_NEEDED:
        break

    print(f"\nĐang tìm theo từ khóa: '{query}'")
    page = 1

    while page <= MAX_PAGES_PER_TERM and downloaded_count < TOTAL_VIDEOS_NEEDED:
        api_url = (
            f"https://api.pexels.com/videos/search?query={query}&per_page={VIDEOS_PER_PAGE}&page={page}"
        )
        try:
            response = request_with_retry(
                api_url,
                headers=headers,
                timeout=SEARCH_TIMEOUT,
                max_retries=MAX_RETRIES,
            )
        except Exception as e:
            print(f"Lỗi API sau nhiều lần thử với từ khóa '{query}': {e}")
            break

        if response.status_code != 200:
            print(f"Lỗi API với từ khóa '{query}': {response.status_code} - {response.text}")
            break

        data = response.json()
        videos = data.get("videos", [])

        if not videos:
            print(f"Đã hết video cho từ khóa '{query}'.")
            break

        for video in videos:
            if downloaded_count >= TOTAL_VIDEOS_NEEDED:
                break

            video_id = video["id"]
            if video_id in seen_ids:
                continue

            video_files = video.get("video_files", [])

            target_file = None
            for file in video_files:
                if file["file_type"] == "video/mp4" and file["quality"] == "hd":
                    target_file = file
                    break

            if not target_file and len(video_files) > 0:
                target_file = video_files[0]

            if target_file:
                video_url = target_file["link"]
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                query_tag = query.replace(" ", "-")
                file_name = os.path.join(OUTPUT_DIR, f"vid_{query_tag}_{video_id}.mp4")
                tmp_file_name = f"{file_name}.part"

                try:
                    print(
                        f"[{downloaded_count + 1}/{TOTAL_VIDEOS_NEEDED}] Đang tải video ID: {video_id} ({query})..."
                    )
                    video_data = request_with_retry(
                        video_url,
                        stream=True,
                        timeout=DOWNLOAD_TIMEOUT,
                        max_retries=MAX_RETRIES,
                    )
                    video_data.raise_for_status()

                    with open(tmp_file_name, 'wb') as f:
                        for chunk in video_data.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)

                    os.replace(tmp_file_name, file_name)

                    downloaded_count += 1
                    seen_ids.add(video_id)
                    time.sleep(1)

                except Exception as e:
                    if os.path.exists(tmp_file_name):
                        os.remove(tmp_file_name)
                    print(f"Lỗi khi tải video {video_id}: {e}")

        page += 1

if downloaded_count < TOTAL_VIDEOS_NEEDED:
    print(
        f"\nChưa đủ {TOTAL_VIDEOS_NEEDED}. Hiện có {downloaded_count} video duy nhất sau khi đã thử hết từ khóa."
    )

print(f"\nTuyệt vời! Đã tải thành công {downloaded_count} video vào thư mục '{OUTPUT_DIR}'.")