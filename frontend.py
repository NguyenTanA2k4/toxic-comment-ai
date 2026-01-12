import streamlit as st
import requests

# Cấu hình trang
st.set_page_config(page_title="AI Kiểm Duyệt Độc Hại", page_icon="🛡️")

st.title("🛡️ Hệ thống Phát hiện Bình luận Độc hại")
st.write("Nhập bình luận bên dưới để AI kiểm tra độ 'sạch' nhé!")

# Cấu hình URL Backend
BACKEND_URL = "http://localhost:8000/predict"
ADD_WORD_URL = "http://localhost:8000/add-word"

# Ô nhập liệu chính
text_input = st.text_area("Nội dung bình luận:", height=100, placeholder="Ví dụ: Bạn thật là tuyệt vời...")

if st.button("Kiểm tra ngay 🚀"):
    if not text_input.strip():
        st.warning("Vui lòng nhập nội dung trước khi kiểm tra!")
    else:
        with st.spinner("AI đang suy nghĩ..."):
            try:
                response = requests.post(BACKEND_URL, json={"text": text_input})
                
                if response.status_code == 200:
                    result = response.json()
                    label = result["label"]
                    score = result["score"] # Đây là điểm Độc hại (0.0 -> 1.0)
                    
                    st.divider()
                    
                    # --- LOGIC HIỂN THỊ MỚI (ĐÃ SỬA) ---
                    if label == "CLEAN":
                        # Lấy 100% trừ đi điểm độc hại để ra điểm An toàn
                        # Ví dụ: Độc hại 0.02 (2%) --> An toàn = 0.98 (98%)
                        safe_score = 1.0 - score
                        st.success(f"✅ **AN TOÀN (CLEAN)** - Độ tin cậy: {safe_score*100:.1f}%")
                        st.balloons()
                        # Thanh hiển thị cũng dùng safe_score cho đẹp
                        st.progress(safe_score)
                        
                    else:
                        # Nếu là Toxic thì giữ nguyên điểm độc hại để cảnh báo
                        if score > 0.85:
                            st.error(f"⛔ **CỰC KỲ NGUY HIỂM!** (Độ tin cậy: {score*100:.1f}%)")
                            st.write("👉 Đề xuất: **CHẶN VĨNH VIỄN**.")
                        elif score > 0.65:
                            st.warning(f"⚠️ **CẢNH BÁO** (Độ tin cậy: {score*100:.1f}%)")
                        else:
                            st.warning(f"🤔 **NGHI VẤN** (Độ tin cậy: {score*100:.1f}%)")
                        
                        st.progress(score)

                else:
                    st.error("Lỗi kết nối đến Server AI!")
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")

# --- SIDEBAR ADMIN (GIỮ NGUYÊN) ---
with st.sidebar:
    st.header("🔧 Admin Panel")
    st.write("Thêm từ cấm nóng")
    admin_pass = st.text_input("Mật khẩu Admin:", type="password")
    if admin_pass == "123456":
        new_word_input = st.text_input("Nhập từ muốn cấm:")
        if st.button("Thêm vào Blacklist"):
            if new_word_input:
                try:
                    resp = requests.post(ADD_WORD_URL, json={"word": new_word_input})
                    if resp.status_code == 200:
                        st.success(resp.json()["message"])
                except:
                    st.error("Lỗi kết nối!")

st.markdown("---")
st.caption("Phát triển bởi Nhóm 22 - IUH | Model: PhoBERT")