# frontend.py
import streamlit as st
import requests

# Cấu hình giao diện
st.set_page_config(page_title="AI Moderator", page_icon="🛡️")

st.title("🛡️ Hệ thống kiểm duyệt bình luận")
st.write("Nhập bình luận để AI kiểm tra độ độc hại (Toxic Detection).")

# URL của Backend (Chạy local thì là localhost)
BACKEND_URL = "http://localhost:8000/predict"

# Form nhập liệu
with st.form("my_form"):
    text_input = st.text_area("Nội dung bình luận:", height=100)
    submitted = st.form_submit_button("Kiểm tra")

    if submitted and text_input:
        with st.spinner("Đang gửi đến AI Server..."):
            try:
                # Gửi request sang Backend
                payload = {"text": text_input}
                response = requests.post(BACKEND_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Hiển thị kết quả dựa trên phản hồi từ Backend
                    st.divider()
                    score = data["confidence_score"] * 100
                    
                    if data["is_toxic"]:
                        st.error(f"⚠️ KẾT QUẢ: {data['message']}")
                        st.progress(int(score), text=f"Độ độc hại: {score:.1f}%")
                    else:
                        st.success(f"✅ KẾT QUẢ: {data['message']}")
                        st.metric(label="Độ an toàn", value=f"{100-score:.1f}%")
                else:
                    st.error("Lỗi kết nối đến Server!")
            except Exception as e:
                st.error(f"Không thể kết nối Backend. Hãy chắc chắn bạn đã chạy file backend.py. Lỗi: {e}")