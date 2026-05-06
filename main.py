from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import HfApi
import os
import shutil
import uvicorn

app = FastAPI()

# Настройки доступа (чтобы сайт на GitHub Pages мог общаться с этим сервером)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ТВОИ НАСТРОЙКИ
REPO_ID = "EmeraldCreator/BlueTok-Storage" 
# Токен мы возьмем из переменных окружения сервера для безопасности
TOKEN = os.environ.get("HF_TOKEN")

api = HfApi()

@app.get("/")
def read_root():
    return {"status": "BlueTok Server Online"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Загрузка в Dataset на Hugging Face
        api.upload_file(
            path_or_fileobj=temp_path,
            path_in_repo=f"videos/{file.filename}",
            repo_id=REPO_ID,
            repo_type="dataset",
            token=TOKEN
        )
        
        raw_url = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/videos/{file.filename}"
        return {"url": raw_url}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/videos")
async def get_videos():
    try:
        files = api.list_repo_files(repo_id=REPO_ID, repo_type="dataset", token=TOKEN)
        video_urls = [
            f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/{f}" 
            for f in files if f.startswith("videos/") and f.endswith(('.mp4', '.mov', '.avi'))
        ]
        return video_urls
    except:
        return []

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
