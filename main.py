from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
import faiss
import sqlite3
import tensorflow as tf
import os
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "pexels_dataset")
DB_PATH = os.path.join(BASE_DIR, "multimedia_vdb.db")
INDEX_PATH = os.path.join(BASE_DIR, "vector_db.index")

app = FastAPI()

# Cho phép React (Vite) gọi API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/pexels_dataset", StaticFiles(directory=DATASET_DIR), name="pexels_dataset")

# Load mô hình AI và CSDL
model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')
index = faiss.read_index(INDEX_PATH)

def extract_query_feature(video_path):
    cap = cv2.VideoCapture(video_path)
    # Lấy 5 frame để trích xuất nhanh
    features = []
    for i in range(5):
        ret, frame = cap.read()
        if not ret: break
        img = cv2.resize(frame, (224, 224))
        img = preprocess_input(np.expand_dims(img, axis=0))
        features.append(model.predict(img, verbose=0).flatten())
    cap.release()
    return np.mean(features, axis=0)

@app.post("/search")
async def search_video(file: UploadFile = File(...)):
    # Lưu file tạm để xử lý
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    # 1. Trích xuất đặc trưng video upload
    query_vec = extract_query_feature(temp_path)
    faiss.normalize_L2(query_vec.reshape(1, -1))
    
    # 2. Tìm kiếm FAISS
    scores, indices = index.search(query_vec.reshape(1, -1).astype('float32'), 5)
    
    # 3. Lấy Metadata từ SQLite
    conn = sqlite3.connect("multimedia_vdb.db")
    cursor = conn.cursor()
    results = []
    for i, idx in enumerate(indices[0]):
        cursor.execute("SELECT file_name, file_path FROM video WHERE id = ?", (int(idx),))
        row = cursor.fetchone()
        if row:
            results.append({"name": row[0], "path": row[1], "score": float(scores[0][i])})
    
    conn.close()
    os.remove(temp_path) # Xóa file tạm
    return {"results": results}