from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote

# ================== CONFIG ==================
DOMAIN = "https://kicksball.com"
START_URL = f"{DOMAIN}/tv"
SAVE_DIR = "output"
OUTPUT_FILE = os.path.join(SAVE_DIR, "kicksball_tv.txt")

# ================== ฟังก์ชันช่วยเหลือ ==================
def format_url(url_path):
    if not url_path:
        return ""
    if url_path.startswith('http'):
        return url_path
    elif url_path.startswith('//'):
        return f"https:{url_path}"
    else:
        return f"{DOMAIN}/{url_path.lstrip('/')}"

def extract_original_image(proxy_url):
    """ถอดรหัสรูปภาพผ่าน Proxy ให้เป็นภาพต้นฉบับ"""
    if '/img/proxy?u=' in proxy_url:
        try:
            parsed = urlparse(proxy_url)
            query_params = parse_qs(parsed.query)
            if 'u' in query_params:
                return unquote(query_params['u'][0])
        except:
            pass
    return format_url(proxy_url)

# ================== ฟังก์ชันดึงข้อมูล ==================
def scrape_kicksball_tv():
    print(f"📡 กำลังเชื่อมต่อไปยัง {START_URL} ด้วยระบบจำลองลายนิ้วมือเบราว์เซอร์ (TLS Fingerprint)...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': DOMAIN
    }
    
    try:
        # 🌟 ใช้ curl_cffi ปลอมแปลง TLS เพื่อหลบเลี่ยง Cloudflare ระดับเครือข่าย
        response = requests.get(START_URL, headers=headers, impersonate="chrome120", timeout=20)
        
        if response.status_code == 403 or "Just a moment" in response.text:
            print("⚠️ ยังคงติดหน้าป้องกันของ Cloudflare ขอสลับพอร์ตเชื่อมต่อสำรอง...")
            # ลองเปลี่ยนมาใช้ตัวเลือกจำลองเบราว์เซอร์แบบอื่น
            response = requests.get(START_URL, headers=headers, impersonate="safari15_3", timeout=20)
            
        response.raise_for_status()
        html_content = response.text
        
    except Exception as e:
        print(f"❌ เชื่อมต่อล้มเหลว: {e}")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    all_groups_data = []
    
    # ดึง Section ของแต่ละหมวดหมู่ทีวี
    sections = soup.find_all('section', class_='tv-section')
    
    if not sections:
        print("⚠️ ไม่พบโครงสร้างรายการทีวีบนหน้าเว็บ (อาจจะยังติดหน้าป้องกัน)")
        return []
        
    for section in sections:
        title_tag = section.find('h2', class_='section-title')
        category_name = title_tag.text.strip() if title_tag else "หมวดหมู่ทั่วไป"
        
        print(f"--------------------------------------------------")
        print(f"📺 หมวดหมู่: {category_name}")
        
        movies_data = []
        cards = section.find_all('a', class_='tv-card')
        
        for card in cards:
            card_href = card.get('href', '')
            full_link = format_url(card_href)
            
            name_tag = card.find('span', class_='tv-name')
            channel_name = name_tag.text.strip() if name_tag else "ไม่ทราบชื่อช่อง"
            
            img_tag = card.find('img')
            raw_img_src = img_tag.get('src', '') if img_tag else ""
            clean_img = extract_original_image(raw_img_src)
            
            movies_data.append({
                "name": channel_name,
                "url": full_link,
                "image": clean_img,
                "referer": DOMAIN,
                "info": category_name,
                "playInNatPlayer": "true"
            })
            
        print(f"✅ ดึงสำเร็จ {len(movies_data)} ช่อง")
        
        # กรองช่องที่ซ้ำ
        unique_movies = []
        seen = set()
        for m in movies_data:
            if m['url'] not in seen:
                seen.add(m['url'])
                unique_movies.append(m)
                
        if unique_movies:
            emoji = "📺"
            if category_name == "กีฬา": emoji = "⚽"
            elif category_name == "ข่าว": emoji = "📰"
            elif category_name == "บันเทิง": emoji = "🎬"
            elif "การ์ตูน" in category_name: emoji = "🧸"
            elif "สาระ" in category_name: emoji = "🌎"
            
            all_groups_data.append({
                "name": f"{emoji} {category_name}",
                "image": "https://kicksball.com/assets/img/favicon.svg",
                "stations": unique_movies
            })
            
    return all_groups_data

# ================== Main Program ==================
if __name__ == "__main__":
    start_time = time.time()
    print("🚀 เริ่มต้นโปรเจกต์ดึงข้อมูลทีวี KicksBall (API Direct Bypass)\n")
    
    groups_data = scrape_kicksball_tv()
    
    if groups_data:
        os.makedirs(SAVE_DIR, exist_ok=True)
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        final_data = {
            "name": "KicksBall Live TV", 
            "author": f"Auto Update ({current_date})", 
            "info": "ดูทีวีออนไลน์ ฟรี ทุกช่อง",
            "image": "https://kicksball.com/assets/img/favicon.svg",
            "groups": groups_data 
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 บันทึกข้อมูลสำเร็จ! ตรวจสอบไฟล์ได้ที่ {OUTPUT_FILE}")
    else:
        print("\n❌ ไม่สามารถสร้างไฟล์ได้ เนื่องจากดึงข้อมูลไม่สำเร็จ")
        exit(1)
        
    elapsed = time.time() - start_time
    print(f"⏱️ ใช้เวลาทำงานทั้งหมด: {elapsed:.2f} วินาที")
