import os
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

def get_driver():
    """เปิดเบราว์เซอร์ด้วย Undetected Chromedriver เพื่อทะลวงกำแพง 403"""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # ปิดการโหลดรูปเพื่อความรวดเร็ว
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    driver_path = ChromeDriverManager().install()
    # 🌟 headless=False จำเป็นมากสำหรับการทะลวงผ่านหน้าจอเสมือน (Xvfb)
    driver = uc.Chrome(driver_executable_path=driver_path, options=options, headless=False)
    driver.set_page_load_timeout(45)
    return driver

# ================== ฟังก์ชันดึงข้อมูล ==================
def scrape_kicksball_tv():
    print(f"⚙️ กำลังเตรียมเบราว์เซอร์ล่องหน (Xvfb)...")
    try:
        driver = get_driver()
    except Exception as e:
        print(f"❌ เปิดเบราว์เซอร์ไม่สำเร็จ: {e}")
        return []

    print(f"📡 กำลังบุกเข้าไปยัง {START_URL} ...")
    try:
        driver.get(START_URL)
        
        # 🌟 รอจนกว่ากล่องหมวดหมู่ทีวีโผล่ขึ้นมา (การันตีว่าผ่านด่านสำเร็จ)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.tv-section'))
        )
        time.sleep(2) # รอเรนเดอร์อีกนิดเพื่อความชัวร์
        html_source = driver.page_source
        print("✅ เจาะทะลุระบบป้องกัน 403 สำเร็จ!")
        
    except Exception as e:
        print(f"❌ โหลดหน้าเว็บไม่สำเร็จ (อาจติดด่าน หรือหมดเวลา): {e}")
        driver.quit()
        return []
    finally:
        driver.quit() # กวาด HTML เสร็จ ปิดเบราว์เซอร์ได้เลย!

    # เริ่มขั้นตอนแกะข้อมูลจาก HTML
    soup = BeautifulSoup(html_source, 'html.parser')
    all_groups_data = []
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
    print("🚀 เริ่มต้นโปรเจกต์ดึงข้อมูลทีวี KicksBall (Xvfb Stealth Scrape)\n")
    
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
