#!/bin/bash

# 1. Chạy Backend (FastAPI) ở chế độ ngầm (background) tại cổng 8000
uvicorn backend:app --host 0.0.0.0 --port 8000 &

# 2. Chờ 5 giây cho Backend khởi động xong
sleep 5

# 3. Chạy Frontend (Streamlit) tại cổng được cung cấp (Render sẽ cấp PORT)
# Nếu không có biến PORT, mặc định dùng 8501
streamlit run frontend.py --server.port=${PORT:-8501} --server.address=0.0.0.0