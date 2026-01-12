# backend.py - FINAL VERSION (Voice + Dashboard + Active Learning)
from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import uvicorn
import re
import os
import pandas as pd
from datetime import datetime
import speech_recognition as sr
import shutil

app = FastAPI()

# --- CẤU HÌNH ---
MODEL_PATH = "./model"
BLACKLIST_FILE = "blacklist.txt"
HISTORY_FILE = "history.csv"
FEEDBACK_FILE = "feedback.csv"
BLACKLIST = []

# Load Model
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

# Load Blacklist
if os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        BLACKLIST = [line.strip().lower() for line in f if line.strip()]

# Tạo file CSV nếu chưa có
if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=["time", "ip", "text", "label", "score"]).to_csv(HISTORY_FILE, index=False)

if not os.path.exists(FEEDBACK_FILE):
    pd.DataFrame(columns=["time", "text", "user_correction"]).to_csv(FEEDBACK_FILE, index=False)

# --- HELPER FUNCTIONS ---
def clean_text(text: str):
    text = text.lower()
    text = re.sub(r'([a-z])\1+', r'\1', text)
    return text

def save_log(ip, text, label, score):
    # Lưu lịch sử vào CSV để vẽ biểu đồ
    new_row = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ip": ip, "text": text, "label": label, "score": score}
    df = pd.DataFrame([new_row])
    df.to_csv(HISTORY_FILE, mode='a', header=False, index=False)

# --- API ENDPOINTS ---

class TextRequest(BaseModel):
    text: str

class FeedbackRequest(BaseModel):
    text: str
    correction: str

@app.post("/predict")
async def predict(data: TextRequest, request: Request):
    text = data.text
    processed_text = clean_text(text)
    
    # Lấy IP
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0] if forwarded else request.client.host

    # 1. Check Blacklist
    if any(word in processed_text for word in BLACKLIST):
        label, score = "TOXIC", 1.0
        save_log(client_ip, text, label, score)
        return {"label": label, "score": score, "method": "BLACKLIST"}

    # 2. AI Predict
    inputs = tokenizer(processed_text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        score = probs[0][1].item()

    label = "TOXIC" if score > 0.5 else "CLEAN"
    save_log(client_ip, text, label, score) # Ghi log
    
    return {"label": label, "score": score, "method": "AI"}

@app.post("/feedback")
async def feedback(data: FeedbackRequest):
    # Lưu phản hồi của người dùng (Dạy ngược AI)
    new_row = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "text": data.text, "user_correction": data.correction}
    df = pd.DataFrame([new_row])
    df.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
    return {"message": "Đã lưu phản hồi. AI sẽ học lại câu này!"}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Xử lý file âm thanh gửi lên
    try:
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_filename) as source:
            audio_data = recognizer.record(source)
            # Dùng Google API (Free) để dịch
            text = recognizer.recognize_google(audio_data, language="vi-VN")
        
        os.remove(temp_filename) # Xóa file tạm
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": str(e)}

@app.get("/stats")
async def get_stats():
    # API trả về dữ liệu cho Dashboard
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        total = len(df)
        toxic_count = len(df[df['label'] == 'TOXIC'])
        clean_count = len(df[df['label'] == 'CLEAN'])
        top_ips = df['ip'].value_counts().head(5).to_dict()
        return {"total": total, "toxic": toxic_count, "clean": clean_count, "top_ips": top_ips}
    return {"total": 0, "toxic": 0, "clean": 0, "top_ips": {}}

@app.post("/add-word")
async def add_word(data: dict):
    word = data.get("word", "").lower().strip()
    if word and word not in BLACKLIST:
        BLACKLIST.append(word)
        return {"message": f"Đã thêm '{word}'", "status": "success"}
    return {"message": "Lỗi", "status": "fail"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)