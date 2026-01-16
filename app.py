import os
import requests
from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- HEDEF URL ---
TARGET_URL = "https://www.cb.com.tr/ilanlar?officeid=470&officeuserid=16801"

# --- TARAYICI KİMLİĞİ ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def clean_text(element):
    if element:
        return element.get_text(strip=True)
    return ""

def fetch_real_estate_data():
    print(f"📡 İstek gönderiliyor: {TARGET_URL}")
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ Bağlantı Hatası: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        listings = []

        # --- YENİ CSS SEÇİCİLER (Analiz Sonucu) ---
        # İlanların ana kutusu "cb-list-item" class'ına sahip
        cards = soup.select('.cb-list-item')

        print(f"🔎 Bulunan İlan Sayısı: {len(cards)}")

        for card in cards:
            try:
                # 1. Başlık
                # Başlık h2 etiketinde duruyor
                title_el = card.select_one('.cb-list-item-info h2')
                title = clean_text(title_el)

                # 2. Fiyat
                # Fiyat "text-primary" class'lı span içinde
                price_el = card.select_one('.feature-item .text-primary')
                price = clean_text(price_el)

                # 3. Link
                # Link başlığın üstündeki 'a' etiketinde
                link_el = card.select_one('.cb-list-img-container a')
                link = link_el['href'] if link_el else "#"
                if link and not link.startswith('http'):
                    link = "https://www.cb.com.tr" + link

                # 4. Resim
                # Resim img etiketinde
                img_el = card.select_one('.cb-list-img-container img')
                img_url = "https://via.placeholder.com/400x300"
                if img_el:
                    img_url = img_el.get('src') or img_el.get('data-src')

                # 5. Lokasyon (İlçe / Mahalle)
                region_el = card.select_one('span[itemprop="addressRegion"]')
                street_el = card.select_one('span[itemprop="streetAddress"]')
                
                region = clean_text(region_el)
                street = clean_text(street_el)
                loc = f"{region}, {street}" if region and street else "Ankara"

                # 6. Özellikler (Oda, m2)
                # İkonlardan (flaticon) yola çıkarak buluyoruz
                rooms = ""
                area = ""
                
                features = card.select('.feature-item')
                for feat in features:
                    text = clean_text(feat)
                    if 'm2' in text or 'm²' in text:
                        area = text
                    elif '+' in text: # 3+1, 5+1 gibi
                        rooms = text

                # Sadece başlığı olan geçerli ilanları ekle
                if title:
                    listings.append({
                        "title": title,
                        "price": price,
                        "loc": loc,
                        "img": img_url,
                        "link": link,
                        "rooms": rooms,
                        "area": area,
                        "type": "Kiralık" if "Kiralık" in title else "Satılık"
                    })

            except Exception as e:
                print(f"⚠️ İlan parse hatası: {e}")
                continue

        return listings

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")
        return []

@app.route('/api/listings', methods=['GET'])
def get_listings():
    data = fetch_real_estate_data()
    return jsonify({"success": True, "data": data})

@app.route('/')
def home():
    try:
        # Dosya adını 'index.html' olarak varsayıyoruz. 
        # Eğer değiştirdiysen burayı güncelle.
        return send_file('index.html')
    except Exception as e:
        return f"Dosya bulunamadı: {e}"

if __name__ == '__main__':
    print("🚀 Sunucu Başlatıldı: http://localhost:5000")
    app.run(debug=True, port=5000)