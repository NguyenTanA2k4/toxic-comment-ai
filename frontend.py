# frontend.py - FINAL VERSION
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Cấu hình
st.set_page_config(page_title="AI Toxic Detector Pro", page_icon="🛡️", layout="wide")
BACKEND_URL = "http://localhost:8000"

# --- SIDEBAR: CHUYỂN ĐỔI CHẾ ĐỘ ---
with st.sidebar:
    st.title("⚙️ Menu Chức Năng")
    mode = st.radio("Chọn chế độ:", ["👤 Người dùng", "🛡️ Quản trị viên (Admin)"])
    
    st.markdown("---")
    st.info("💡 Mẹo: Dùng Micro để nói thay vì gõ!")

# --- CHẾ ĐỘ 1: NGƯỜI DÙNG (USER) ---
if mode == "👤 Người dùng":
    st.title("🛡️ AI Phát Hiện Bình Luận Độc Hại")
    st.write("Hệ thống tích hợp: Voice Input 🎤 + Active Learning 🧠")

    # 1. INPUT: Chọn Gõ phím hoặc Nói
    input_type = st.radio("Bạn muốn nhập liệu bằng cách nào?", ["⌨️ Gõ văn bản", "🎤 Nói (Voice)"], horizontal=True)
    
    user_text = ""

    if input_type == "⌨️ Gõ văn bản":
        user_text = st.text_area("Nhập nội dung:", height=100)
    else:
        # TÍNH NĂNG VOICE INPUT (MỚI)
        audio_value = st.audio_input("Nhấn nút đỏ để ghi âm")
        if audio_value:
            with st.spinner("Đang nghe và dịch sang chữ..."):
                files = {"file": ("voice.wav", audio_value, "audio/wav")}
                try:
                    res = requests.post(f"{BACKEND_URL}/transcribe", files=files)
                    if res.status_code == 200:
                        transcribed = res.json().get("text", "")
                        if transcribed:
                            st.success(f"🗣️ Bạn đã nói: '{transcribed}'")
                            user_text = transcribed
                        else:
                            st.warning("Không nghe rõ, vui lòng nói lại!")
                except:
                    st.error("Lỗi kết nối Mic!")

    # 2. NÚT KIỂM TRA
    if st.button("Kiểm tra ngay 🚀", type="primary"):
        if not user_text:
            st.warning("Chưa có nội dung!")
        else:
            with st.spinner("AI đang phân tích..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/predict", json={"text": user_text})
                    if resp.status_code == 200:
                        data = resp.json()
                        label = data["label"]
                        score = data["score"]
                        
                        st.divider()
                        
                        # Hiển thị kết quả
                        if label == "CLEAN":
                            safe_score = 1.0 - score
                            st.success(f"✅ **AN TOÀN** (Độ tin cậy: {safe_score*100:.1f}%)")
                            st.balloons()
                        else:
                            st.error(f"⛔ **ĐỘC HẠI (TOXIC)** (Độ tin cậy: {score*100:.1f}%)")
                            if score > 0.85:
                                st.write("👉 Đề xuất: **CHẶN NGAY**")
                        
                        # --- TÍNH NĂNG ACTIVE LEARNING (DẠY NGƯỢC) ---
                        with st.expander("Báo cáo kết quả sai? (Giúp AI học tốt hơn)"):
                            with st.form("feedback_form"):
                                st.write(f"Bạn cho rằng kết quả **{label}** là sai?")
                                correct_label = st.selectbox("Theo bạn, nhãn đúng là gì?", ["CLEAN (Tốt)", "TOXIC (Xấu)"])
                                if st.form_submit_button("Gửi phản hồi"):
                                    requests.post(f"{BACKEND_URL}/feedback", json={"text": user_text, "correction": correct_label})
                                    st.success("Cảm ơn! Dữ liệu đã được lưu để huấn luyện lại AI.")
                except Exception as e:
                    st.error(f"Lỗi Server: {e}")

# --- CHẾ ĐỘ 2: ADMIN DASHBOARD (THỐNG KÊ) ---
else:
    st.title("📊 Dashboard Quản Trị Hệ Thống")
    password = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    if password == "123456":
        st.success("Đăng nhập thành công!")
        
        # Gọi API lấy thống kê
        try:
            res = requests.get(f"{BACKEND_URL}/stats")
            if res.status_code == 200:
                stats = res.json()
                
                # 1. Metrics tổng quan
                col1, col2, col3 = st.columns(3)
                col1.metric("Tổng request", stats["total"])
                col2.metric("Số câu Độc hại", stats["toxic"])
                col3.metric("Số câu An toàn", stats["clean"])
                
                st.divider()
                
                # 2. Biểu đồ tròn (Toxic vs Clean)
                st.subheader("Tỷ lệ nội dung")
                if stats["total"] > 0:
                    fig, ax = plt.subplots()
                    ax.pie([stats["toxic"], stats["clean"]], labels=["Toxic", "Clean"], autopct='%1.1f%%', colors=["#ff4b4b", "#60b4ff"])
                    st.pyplot(fig)
                else:
                    st.info("Chưa có dữ liệu để vẽ biểu đồ.")
                
                # 3. Top IP phá hoại
                st.subheader("🚨 Top IP có hành vi kiểm tra nhiều nhất")
                st.write(stats["top_ips"])
                
                # 4. Thêm từ cấm
                st.subheader("🔧 Cấu hình Blacklist")
                new_word = st.text_input("Thêm từ cấm mới:")
                if st.button("Thêm từ"):
                    requests.post(f"{BACKEND_URL}/add-word", json={"word": new_word})
                    st.success(f"Đã thêm '{new_word}' vào danh sách đen!")

        except:
            st.error("Không kết nối được Server!")
    elif password:
        st.error("Sai mật khẩu!")