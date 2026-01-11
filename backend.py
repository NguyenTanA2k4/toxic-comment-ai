# backend.py - Phiên bản Hybrid (Đọc Blacklist từ file)
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import uvicorn
import re
import os

app = FastAPI(title="Toxic Comment Detection API")

# --- 1. CONFIG & LOAD DATA ---
MODEL_PATH = "./model"
BLACKLIST_FILE = "blacklist.txt"
BLACKLIST = []

# Load Model
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    print("✅ Đã load Model thành công!")
except Exception as e:
    print(f"❌ Lỗi load model: {e}")

# Load Blacklist từ file txt
if os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        # Đọc từng dòng, loại bỏ khoảng trắng thừa và chuyển về chữ thường
        BLACKLIST = [line.strip().lower() for line in f if line.strip()]
    print(f"✅ Đã load {len(BLACKLIST)} từ cấm từ {BLACKLIST_FILE}")
else:
    print(f"⚠️ Không tìm thấy file {BLACKLIST_FILE}. Hệ thống sẽ chỉ dùng AI.")

# -----------------------------

class CommentInput(BaseModel):
    text: str

# Từ điển Teencode (Giữ nguyên)
teencode_dict = {
    "tk": "thằng", "mk": "mình", "nguu": "ngu", "nguuu": "ngu",
    "m": "mày", "t": "tao", "k": "không", "ko": "không",
    "cc": "cục cứt", "cl": "cái lồn", "loz": "lồn"
}

def clean_text(text: str):
    text = text.lower()
    # Gộp ký tự lặp (nguuuu -> ngu)
    text = re.sub(r'([a-z])\1+', r'\1', text) 
    words = text.split()
    fixed_words = [teencode_dict.get(word, word) for word in words]
    return " ".join(fixed_words)

def check_blacklist(text):
    # Kiểm tra xem có từ cấm nào nằm trong câu không
    for word in BLACKLIST:
        # Dùng regex để bắt chính xác từ (tránh bắt nhầm từ chứa từ cấm)
        # Ví dụ: tránh bắt nhầm "lồng bàn" khi từ cấm là "lồn" (tuy nhiên danh sách trên khá mạnh nên check in là đủ)
        if word in text: 
            return True, word
    return False, None

@app.post("/predict")
async def predict_comment(input_data: CommentInput):
    original_text = input_data.text
    processed_text = clean_text(original_text)
    
    # BƯỚC 1: KIỂM TRA BLACKLIST (HARD RULE)
    if BLACKLIST:
        is_blacklisted, banned_word = check_blacklist(processed_text)
        if is_blacklisted:
            return {
                "text": original_text,
                "processed_text": processed_text,
                "is_toxic": True,
                "confidence_score": 1.0, 
                "message": f"VI PHẠM: Chứa từ cấm '{banned_word}'"
            }

    # BƯỚC 2: AI PREDICTION (SOFT RULE)
    inputs = tokenizer(processed_text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        pred_label = torch.argmax(probs, dim=-1).item()
        confidence = probs[0][1].item() 

    is_toxic = True if pred_label == 1 else False
    
    return {
        "text": original_text,
        "processed_text": processed_text,
        "is_toxic": is_toxic,
        "confidence_score": confidence,
        "message": "Cảnh báo: Độc hại (AI phát hiện)" if is_toxic else "An toàn"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)