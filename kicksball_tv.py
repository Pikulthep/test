import os
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from seleniumbase import SB

# ================== CONFIG ==================
DOMAIN = "https://kicksball.com"
START_URL = f"{DOMAIN}/tv"
SAVE_DIR = "output"
OUTPUT_FILE = os.path.join(SAVE_DIR, "kicksball_tv.txt")

# ================== ฟังก์ชันช่วยเหลือ ==================
def format_url(url_path):
    if not url_path: return ""
    if url_path.startswith('http'): return url_path
    elif url_path.startswith('//'): return f"https:{url_path}"
    else: return f"{DOMAIN}/{url_path.lstrip('/')}"

def extract_original_image(proxy_url):
    """ถอดรหัสรูปภาพที่ถูกหุ้มด้วย Proxy กลับเป็น URL ต้นฉบับ"""
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
    print("⚙️ กำลังเตรียมเบราว์เซอร์ขั้นสุดยอด (SeleniumBase UC Mode)...")
    all_groups_data = []

    # 🌟 พระเอกของเรา: เปิดเบราว์เซอร์ด้วย SeleniumBase โหมด UC (Undetected)
    try:
        with SB(uc=True, headless=False) as sb:
            print(f"📡 กำลังบุกเข้าไปยัง {START_URL} ...")
            
            # ใช้ท่าไม้ตาย: เปิดเว็บและต่อเน็ตใหม่ซ้ำๆ เพื่อสลัดการจับตามองของ Cloudflare
            sb.uc_open_with_reconnect(START_URL, reconnect_time=4)
            
            print("⏳ เจอหน้า Just a moment... กำลังสั่งให้ AI คลิกปุ่ม 'ฉันเป็นมนุษย์' ...")
            try:
                # 🌟 ฟังก์ชันหาและคลิกกล่อง Captcha ให้อัตโนมัติ!
                sb.uc_gui_click_captcha()
                time.sleep(3)
            except:
                pass # ถ้าโชคดีไม่มีกล่องให้คลิก ก็ปล่อยผ่านไปเลย
                
            try:
                # รอจนกว่าจะโหลดผ่านเข้ามาเจอโครงสร้างทีวี
                sb.wait_for_element('.tv-section', timeout=20)
                html_source = sb.get_page_source()
                print("✅ ทะลวงหน้า Just a moment สำเร็จ! เข้าถึงข้อมูลแล้ว")
            except Exception as e:
                print("❌ ทะลวงด่าน Cloudflare ไม่สำเร็จ (IP ของ GitHub อาจจะโดนแบนถาวร)")
                print("🔍 Snapshot:", sb.get_page_source()[:500])
                return []
                
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเปิดเบราว์เซอร์: {e}")
        return []

    # ================== เริ่มขั้นตอนแกะข้อมูลจาก HTML ==================
    print("⛏️ กำลังสกัดข้อมูลทีวีทั้งหมด...")
    soup = BeautifulSoup(html_source, 'html.parser')
    sections = soup.find_all('section', class_='tv-section')

    if not sections:
        print("⚠️ ไม่พบโครงสร้างรายการทีวีบนหน้าเว็บ")
        return []

    for section in sections:
        title_tag = section.find('h2', class_='section-title')
        category_name = title_tag.text.strip() if title_tag else "หมวดหมู่ทั่วไป"
        
        print(f"--------------------------------------------------")
        print(f"📺 หมวดหมู่: {category_name}")
        
        movies_data = []
        cards = section.find_all('a', class_='tv-card')
        
        for card in cards:
            full_link = format_url(card.get('href', ''))
            name_tag = card.find('span', class_='tv-name')
            channel_name = name_tag.text.strip() if name_tag else "ไม่ทราบชื่อช่อง"
            
            img_tag = card.find('img')
            clean_img = extract_original_image(img_tag.get('src', '') if img_tag else "")
            
            movies_data.append({
                "name": channel_name,
                "url": full_link,
                "image": clean_img,
                "referer": DOMAIN,
                "info": category_name,
                "playInNatPlayer": "true"
            })
            
        print(f"✅ ดึงสำเร็จ {len(movies_data)} ช่อง")
        
        # กรองตัวซ้ำ
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
    print("🚀 เริ่มต้นโปรเจกต์ดึงข้อมูลทีวี KicksBall (SeleniumBase Auto-Clicker)\n")
    
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
