import requests
import random
import time
from datetime import datetime, timedelta

# Test verisi ekleme scripti
def add_test_data():
    base_url = "http://localhost:5000"
    
    # Test verileri
    sensors = [
        {"id": "SENSOR001", "lokasyon": "Ofis A"},
        {"id": "SENSOR002", "lokasyon": "Ofis B"},
        {"id": "SENSOR003", "lokasyon": "Depo"},
        {"id": "SENSOR004", "lokasyon": "Laboratuvar"}
    ]
    
    print("Test verileri ekleniyor...")
    
    for i in range(50):  # 50 test verisi
        for sensor in sensors:
            # Gerçekçi sıcaklık ve nem değerleri
            sicaklik = random.uniform(18, 35)
            nem = random.uniform(40, 80)
            
            data = {
                "sensor_id": sensor["id"],
                "sicaklik": round(sicaklik, 1),
                "nem": round(nem, 1),
                "lokasyon": sensor["lokasyon"]
            }
            
            try:
                response = requests.post(f"{base_url}/api/add_data", json=data)
                if response.status_code == 200:
                    print(f"Veri eklendi: {sensor['lokasyon']} - {sicaklik}°C, {nem}%")
                else:
                    print(f"Hata: {response.status_code}")
            except Exception as e:
                print(f"Bağlantı hatası: {e}")
            
            time.sleep(0.1)  # Kısa bekleme
    
    print("Test verileri eklendi!")

if __name__ == "__main__":
    add_test_data()
