import os

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_FOLDER = os.path.join(BASE_DIR, "pexels_dataset")
SAVE_PATH = os.path.join(BASE_DIR, "video_features_db.npy")
FILE_NAMES_PATH = os.path.join(BASE_DIR, "video_names_db.npy")

NUM_KEYFRAMES = 5


def build_model():
    print("Đang tải mô hình MobileNetV2...")
    return MobileNetV2(weights="imagenet", include_top=False, pooling="avg")


model = build_model()


def extract_features_from_video(video_path, num_keyframes=NUM_KEYFRAMES):
    """Trích xuất vector đặc trưng từ một file video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return None

    frame_indices = np.linspace(0, total_frames - 1, num_keyframes, dtype=int)
    video_features = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        img = cv2.resize(frame, (224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        feature = model.predict(img_array, verbose=0)
        video_features.append(feature.flatten())

    cap.release()

    if not video_features:
        return None

    return np.mean(video_features, axis=0)


def main():
    if not os.path.isdir(VIDEO_FOLDER):
        raise FileNotFoundError(f"Không tìm thấy thư mục video: {VIDEO_FOLDER}")

    video_files = sorted(
        file_name for file_name in os.listdir(VIDEO_FOLDER) if file_name.lower().endswith(".mp4")
    )

    print(f"Bắt đầu trích xuất đặc trưng từ {len(video_files)} video...")

    all_features = []
    all_names = []

    for index, file_name in enumerate(video_files, start=1):
        video_path = os.path.join(VIDEO_FOLDER, file_name)
        try:
            feature_vector = extract_features_from_video(video_path)
            if feature_vector is None:
                print(f"[{index}/{len(video_files)}] Bỏ qua: {file_name} (không đọc được frame hợp lệ)")
                continue

            all_features.append(feature_vector)
            all_names.append(file_name)
            print(f"[{index}/{len(video_files)}] Đã xử lý: {file_name}")

        except Exception as error:
            print(f"[{index}/{len(video_files)}] Lỗi với {file_name}: {error}")

    if not all_features:
        print("Không trích xuất được feature nào.")
        return

    all_features = np.array(all_features)
    all_names = np.array(all_names)

    np.save(SAVE_PATH, all_features)
    np.save(FILE_NAMES_PATH, all_names)

    print(f"\nHoàn thành! Đã trích xuất {len(all_features)} vector đặc trưng.")
    print(f"Dữ liệu đã được lưu vào {SAVE_PATH} và {FILE_NAMES_PATH}")


if __name__ == "__main__":
    main()
import cv2
import numpy as np
import os
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image

# 1. Khởi tạo mô hình (Bỏ phần phân loại cuối cùng, chỉ lấy lớp đặc trưng - Bottleneck layer)
model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

def extract_features_from_video(video_path, num_keyframes=5):
    """
    Trích xuất vector đặc trưng từ một file video.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Tính toán vị trí các frame cần lấy (ví dụ lấy 5 frame trải đều video)
    frame_indices = np.linspace(0, total_frames - 1, num_keyframes, dtype=int)
    
    video_features = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
            
        # Tiền xử lý ảnh cho MobileNetV2
        img = cv2.resize(frame, (224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        # Trích xuất đặc trưng của 1 frame (vector 1280 chiều)
        feature = model.predict(img_array, verbose=0)
        video_features.append(feature.flatten())
    
    cap.release()
    
    if len(video_features) == 0:
        return None
        
    # Tính trung bình cộng (Average Pooling) để ra vector đại diện cho cả video
    return np.mean(video_features, axis=0)

# --- CHẠY TRÍCH XUẤT CHO TOÀN BỘ 550 VIDEO ---
VIDEO_FOLDER = "pexels_dataset"
SAVE_PATH = "video_features_db.npy" # Lưu lại để Thành viên 2 sử dụng
FILE_NAMES_PATH = "video_names_db.npy"

all_features = []
all_names = []

print("Bắt đầu trích xuất đặc trưng... (Quá trình này có thể mất vài phút)")

for file_name in os.listdir(VIDEO_FOLDER):
    if file_name.endswith(".mp4"):
        video_path = os.path.join(VIDEO_FOLDER, file_name)
        feature_vector = extract_features_from_video(video_path)
        
        if feature_vector is not None:
            all_features.append(feature_vector)
            all_names.append(file_name)
            print(f"Đã xử lý: {file_name}")

# Chuyển sang định dạng numpy để lưu trữ
all_features = np.array(all_features)
all_names = np.array(all_names)

# Lưu lại file để chuyển giao cho Thành viên 2 (Backend)
np.save(SAVE_PATH, all_features)
np.save(FILE_NAMES_PATH, all_names)

print(f"\nHoàn thành! Đã trích xuất {len(all_features)} vector đặc trưng.")
print(f"Dữ liệu đã được lưu vào {SAVE_PATH} và {FILE_NAMES_PATH}")