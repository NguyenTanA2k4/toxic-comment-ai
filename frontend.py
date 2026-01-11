import streamlit as st
import requests

# Cấu hình tiêu đề trang web
st.set_page_config(page_title="AI Kiểm Duyệt Độc Hại", page_icon="🛡️")

# Tiêu đề chính
st.title("🛡️ Hệ thống Phát hiện Bình luận Độc hại")
st.write("Nhập bình luận bên dưới để AI kiểm tra độ 'sạch' nhé!")

# URL của Backend (Khi chạy Docker chung thì dùng localhost)
BACKEND_URL = "http://localhost:8000/predict"

# Ô nhập liệu
text_input = st.text_area("Nội dung bình luận:", height=100, placeholder="Ví dụ: Bạn thật là tuyệt vời...")

if st.button("Kiểm tra ngay 🚀"):
    if not text_input.strip():
        st.warning("Vui lòng nhập nội dung trước khi kiểm tra!")
    else:
        with st.spinner("AI đang suy nghĩ..."):
            try:
                # Gửi yêu cầu sang Backend
                response = requests.post(BACKEND_URL, json={"text": text_input})
                
                if response.status_code == 200:
                    result = response.json()
                    label = result["label"]
                    score = result["score"]
                    
                    # --- PHẦN MỚI: XỬ LÝ MÀU SẮC DỰA TRÊN ĐỘ NGUY HIỂM ---
                    st.divider() # Kẻ 1 đường gạch ngang cho đẹp
                    
                    if label == "CLEAN":
                        # Trường hợp An toàn: Màu XANH
                        clean_confidence = 1 - score
                        
                        st.success(f"✅ **AN TOÀN (CLEAN)** - Độ tin cậy: {clean_confidence*100:.1f}%")
                        st.balloons() # Thả bóng bay chúc mừng
                        
                    else:
                        # Trường hợp Độc hại (TOXIC)
                        if score > 0.85:
                            # Mức độ cao (>85%): Màu ĐỎ (Rất nguy hiểm)
                            st.error(f"⛔ **CỰC KỲ NGUY HIỂM!** (Độ tin cậy: {score*100:.1f}%)")
                            st.write("👉 Đề xuất: **CHẶN VĨNH VIỄN** tài khoản này.")
                        
                        elif score > 0.65:
                             # Mức độ trung bình (65% - 85%): Màu CAM (Cảnh báo)
                            st.warning(f"⚠️ **CẢNH BÁO: NGÔN TỪ KHÔNG PHÙ HỢP** (Độ tin cậy: {score*100:.1f}%)")
                            st.write("👉 Đề xuất: Ẩn bình luận và nhắc nhở.")
                            
                        else:
                            # Mức độ thấp/Lưỡng lự (50% - 65%): Màu VÀNG
                            st.warning(f"🤔 **NGHI VẤN** (Độ tin cậy: {score*100:.1f}%)")
                            st.write("👉 AI cảm thấy câu này hơi tiêu cực, cần người xem xét lại.")

                    # Hiện thanh đo mức độ (Progress Bar)
                    st.write("Thanh đo mức độ tin cậy của AI:")
                    st.progress(score)

                else:
                    st.error("Lỗi kết nối đến Server AI!")
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")

# Thêm thông tin footer
st.markdown("---")
st.caption("Phát triển bởi Nhóm 22 - IUH | Model: PhoBERT")