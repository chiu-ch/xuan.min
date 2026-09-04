import os
import re
import json
import requests
from bs4 import BeautifulSoup

html_path = "index.html"
json_path = "rooms.json"

if not os.path.exists(html_path):
    print("❌ 錯誤：找不到 index.html 檔案")
    exit(1)

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 讀取現有的 json 狀態
room_status = {}
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as jf:
        try:
            room_status = json.load(jf)
        except:
            room_status = {}

has_changed = False
room_links = soup.find_all("a", attrs={"data-room": True})

print("🚀 開始自動檢測 VIP 招待所房間人數...")
for link in room_links:
    room_id = link["data-room"]
    line_url = link["href"]
    
    try:
        response = requests.get(line_url, headers=headers, timeout=15)
        if response.status_code == 200:
            member_match = re.search(r'content="[^"]*成員\s*[:：]\s*([\d,]+)\s*人', response.text)
            if not member_match:
                member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)\s*人", response.text)
            if not member_match:
                member_match = re.search(r"成員\s*[:：]?\s*([\d,]+)", response.text)
            if not member_match:
                member_match = re.search(r'"memberCount"\s*:\s*(\d+)', response.text)

            if member_match:
                current_members = int(member_match.group(1).replace(",", ""))
                is_busy = current_members >= 4  # 4人以上為忙碌 (BUSY)
                
                print(f"房號 {room_id} ｜ 人數：{current_members}人 ｜ 狀態：{'🔴 忙碌' if is_busy else '🟢 空閒'}")
                
                if room_status.get(room_id) != is_busy:
                    room_status[room_id] = is_busy
                    has_changed = True
            else:
                print(f"⚠️ 房號 {room_id} ｜ 無法解析人數結構")
        else:
            print(f"❌ 房號 {room_id} ｜ 請求失敗，狀態碼：{response.status_code}")
    except Exception as e:
        print(f"💥 房號 {room_id} ｜ 連線異常：{e}")

# 儲存最新的 json 狀態
if has_changed:
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(room_status, jf, ensure_ascii=False, indent=2)
    print("\n✅ 房間狀態有變更，已更新 rooms.json！")
else:
    print("\n☕ 掃描完畢：無任何狀態變更。")
