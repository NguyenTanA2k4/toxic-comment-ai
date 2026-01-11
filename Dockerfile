# 1. Dùng Python 3.9 bản nhẹ (Slim)
FROM python:3.9-slim

# 2. Thiết lập thư mục làm việc
WORKDIR /app

# 3. Copy file thư viện và cài đặt
COPY requirements.txt .
# Cài đặt thư viện (thêm --no-cache-dir để giảm dung lượng rác)
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy toàn bộ code và model vào
COPY . .

# 5. Cấp quyền chạy cho file run.sh
RUN chmod +x run.sh

# 6. Mở cổng kết nối (Render tự động map vào biến $PORT)
EXPOSE 8501

# 7. Lệnh chạy khi khởi động
CMD ["./run.sh"]