import os

# Windows'ta dosya adı Türkçe olduğu için mutlak import kullanıyoruz
from ısı import app as application  # gunicorn 'application' isimli WSGI objesini bekler

# Opsiyonel: production port/host ayarları çoğu PaaS'ta çevre değişkenlerinden gelir
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))


