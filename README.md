# Isı Takip Sistemi

Bu proje, gerçek zamanlı sıcaklık ve nem takibi için geliştirilmiş bir web uygulamasıdır. Flask framework'ü kullanılarak oluşturulmuştur.

## Özellikler

- **Gerçek Zamanlı Veri Takibi**: Sıcaklık ve nem verilerini anlık olarak izleme
- **Veritabanı Entegrasyonu**: SQLite veritabanı ile güvenli veri saklama
- **Kullanıcı Yönetimi**: Admin ve User rolleri ile farklı yetki seviyeleri
- **E-posta Bildirimleri**: Yüksek sıcaklık durumunda otomatik uyarılar
- **Responsive Tasarım**: Mobil ve masaüstü uyumlu modern arayüz
- **REST API**: Sensör verilerini almak için API desteği

## Kurulum

1. **Gerekli paketleri yükleyin:**
```bash
pip install -r requirements.txt
```

2. **Uygulamayı çalıştırın:**
```bash
python ısı.py
```

3. **Tarayıcınızda şu adresi açın:**
```
http://localhost:5000
```

## Varsayılan Kullanıcılar

- **Admin**: admin / admin123
- **User**: user / user123

## API Kullanımı

### Yeni Veri Ekleme
```bash
POST /api/add_data
Content-Type: application/json

{
    "sensor_id": "SENSOR001",
    "sicaklik": 25.5,
    "nem": 60.2,
    "lokasyon": "Ofis A"
}
```

### Veri Listesi
```bash
GET /api/data?page=1&per_page=20
```

## E-posta Bildirimleri

E-posta bildirimlerini kullanmak için:

1. `ısı.py` dosyasındaki e-posta ayarlarını güncelleyin:
```python
sender_email = "your-email@gmail.com"
sender_password = "your-app-password"
```

2. Gmail için uygulama şifresi oluşturun:
   - Gmail hesabınızda 2FA'yı etkinleştirin
   - Uygulama şifreleri bölümünden yeni şifre oluşturun

## Veritabanı

Sistem SQLite veritabanı kullanır. Veritabanı dosyası (`isi_takip.db`) otomatik olarak oluşturulur.

## Güvenlik

- Şifreler hash'lenerek saklanır
- Kullanıcı oturumları güvenli şekilde yönetilir
- Admin paneline sadece admin kullanıcıları erişebilir

## Lisans
## GitHub Pages (Statik Önizleme)

Bu depo, dinamik Flask uygulamasına ek olarak GitHub Pages ile açılabilecek statik bir önizleme içerir.

- Statik dosyalar `docs/` klasöründedir.
- GitHub Pages ayarlarında Source olarak "Deploy from a branch" → Branch: `main` ve Folder: `/docs` seçin.
- Canlı sayfada çalışacak dosyalar: `docs/index.html` ve `docs/dashboard.html`.
  - Bu sayfalar örnek verilerle (backend olmadan) çalışır.
  - Gerçek zamanlı, giriş ve veritabanı özellikleri için uygulamayı bir PaaS üzerinde (Render/Railway/Heroku) çalıştırın.

### VSCode Go Live

VSCode Live Server eklentisiyle sadece statik önizlemeyi açmak için:

1. `docs/index.html` dosyasını açın.
2. Sağ alttaki "Go Live" butonuna basın.
3. Statik demo anında görüntülenir. Dinamik backend özellikleri statikte çalışmaz.


Bu proje MIT lisansı altında lisanslanmıştır.
