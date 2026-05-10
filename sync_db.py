import sqlite3
import numpy as np
import faiss
import os

# 1. Load dữ liệu từ Giai đoạn 2
features = np.load("video_features_db.npy").astype('float32')
names = np.load("video_names_db.npy")
total = len(names)
video_ids = np.arange(1, total + 1).astype(np.int64)

# 2. Cấu hình SQLite (Sử dụng file .db bạn đã tạo)
conn = sqlite3.connect("multimedia_vdb.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM video") # Xóa dữ liệu cũ để nạp mới từ đầu

data_to_insert = [(int(video_ids[i]), str(names[i]), f"pexels_dataset/{names[i]}") for i in range(total)]
cursor.executemany("INSERT INTO video (id, file_name, file_path) VALUES (?, ?, ?)", data_to_insert)
conn.commit()
conn.close()

# 3. Cấu hình FAISS IndexIDMap
dimension = features.shape[1]
faiss.normalize_L2(features)
index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
index.add_with_ids(features, video_ids)
faiss.write_index(index, "vector_db.index")

print(f"Đã đồng bộ {total} video vào hệ thống.")