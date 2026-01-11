# backend.py - PHIÊN BẢN HOÀN HẢO (IP Log + Hybrid + Fix Frontend)
from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import uvicorn
import re
import os

app = FastAPI(title="Toxic Comment Detection API")

# --- 1. CẤU HÌNH & LOAD DATA ---
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

# Load Blacklist
if os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        BLACKLIST = [line.strip().lower() for line in f if line.strip()]
    print(f"✅ Đã load {len(BLACKLIST)} từ cấm từ {BLACKLIST_FILE}")
else:
    print(f"⚠️ Không tìm thấy {BLACKLIST_FILE}. Chỉ dùng AI.")

# --- 2. HÀM XỬ LÝ TEXT ---
teencode_dict = {
    "tk": "thằng", "mk": "mình", "nguu": "ngu", "nguuu": "ngu",
    "m": "mày", "t": "tao", "k": "không", "ko": "không",
    "cc": "cục cứt", "cl": "cái lồn", "loz": "lồn", "dm": "địt mẹ", "vcl": "vãi cả lồn"
}

def clean_text(text: str):
    text = text.lower()
    text = re.sub(r'([a-z])\1+', r'\1', text) 
    words = text.split()
    fixed_words = [teencode_dict.get(word, word) for word in words]
    return " ".join(fixed_words)

def check_blacklist(text):
    for word in BLACKLIST:
        if word in text: 
            return True, word
    return False, None

# Input Model
class TextRequest(BaseModel):
    text: str

@app.get("/")
def home():
    return {"message": "Server đang chạy ngon lành!"}

# --- 3. API DỰ ĐOÁN (CÓ TRACKING IP) ---
@app.post("/predict")
async def predict(data: TextRequest, request: Request):
    original_text = data.text
    
    # === A. BẮT ĐỊA CHỈ IP ===
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0]
    else:
        client_ip = request.client.host
    
    print(f"👀 IP [{client_ip}] đang check: '{original_text}'", flush=True)
    # ==========================

    # Xử lý văn bản
    processed_text = clean_text(original_text)
    
    # BƯỚC 1: KIỂM TRA BLACKLIST
    is_toxic = False
    score = 0.0
    label = "CLEAN"
    
    if BLACKLIST:
        is_blacklisted, banned_word = check_blacklist(processed_text)
        if is_blacklisted:
            is_toxic = True
            score = 1.0 # Max điểm vì trúng từ cấm
            label = "TOXIC"
            print(f"   -> ⛔ BỊ CHẶN BỞI BLACKLIST (Từ: {banned_word})", flush=True)
            return {"label": label, "score": score}

    # BƯỚC 2: AI DỰ ĐOÁN
    inputs = tokenizer(processed_text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        score = probs[0][1].item() # Lấy điểm Toxic

    if score > 0.5:
        label = "TOXIC"
    else:
        label = "CLEAN"

    print(f"   -> 🤖 AI chấm điểm: {label} ({score:.2f})", flush=True)

    return {"label": label, "score": score}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)