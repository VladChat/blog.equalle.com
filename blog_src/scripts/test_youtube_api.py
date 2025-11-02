# blog_src/scripts/test_youtube_api.py
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Загружаем ключ из .env
load_dotenv()
api_key = os.getenv("YT_API_KEY")

if not api_key:
    print("❌ API key not found. Please check your .env file.")
    exit()

# Создаём клиент YouTube API
youtube = build("youtube", "v3", developerKey=api_key)

# Тестовый запрос
query = "wet sanding ceramics silicon carbide"

request = youtube.search().list(
    part="snippet",
    q=query,
    maxResults=5,
    relevanceLanguage="en",
    type="video",
    videoDuration="medium"
)
response = request.execute()

# Выводим результаты
print("\n✅ YouTube API connected successfully!\n")
for item in response["items"]:
    title = item["snippet"]["title"]
    channel = item["snippet"]["channelTitle"]
    video_id = item["id"]["videoId"]
    print(f"{title} — {channel}")
    print(f"https://www.youtube.com/watch?v={video_id}\n")
