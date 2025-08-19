from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///isi_takip.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@app.template_filter('tr_time')
def tr_time(dt):
    try:
        return (dt + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return ''

# Veritabanı modelleri
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' veya 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class IsiVerisi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.String(50), nullable=False)
    sicaklik = db.Column(db.Float, nullable=False)
    nem = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lokasyon = db.Column(db.String(100), nullable=False)

class BildirimAyarlari(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    max_sicaklik = db.Column(db.Float, default=30.0)
    email_bildirim = db.Column(db.Boolean, default=True)
    admin_email = db.Column(db.String(120), nullable=False)
    # Lokasyon bazlı e-posta adresleri
    email_ofis = db.Column(db.String(120))  # Ofis A ve Ofis B için ortak
    email_depo = db.Column(db.String(120))
    email_laboratuvar = db.Column(db.String(120))
    # SMTP ayarları
    smtp_server = db.Column(db.String(120), default='smtp.gmail.com')
    smtp_port = db.Column(db.Integer, default=587)
    smtp_email = db.Column(db.String(120))
    smtp_password = db.Column(db.String(255))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# E-posta gönderme fonksiyonu
def send_email_notification(subject, message, to_email):
    try:
        # Veritabanındaki SMTP ayarlarını kullan
        ayarlar = BildirimAyarlari.query.first()
        if not ayarlar or not ayarlar.smtp_email or not ayarlar.smtp_password:
            print("E-posta gönderme hatası: SMTP bilgileriniz eksik (admin panelinden ayarlayın)")
            return False

        smtp_server = ayarlar.smtp_server or "smtp.gmail.com"
        smtp_port = ayarlar.smtp_port or 587
        sender_email = ayarlar.smtp_email
        sender_password = ayarlar.smtp_password

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain', 'utf-8'))

        # TLS 587 akışı
        if int(smtp_port) == 587:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
        else:
            # SSL 465 akışı
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
            server.ehlo()
            server.login(sender_email, sender_password)

        server.sendmail(sender_email, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"E-posta gönderme hatası: {e}")
        return False

# Ana sayfa
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Giriş sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Başarıyla giriş yaptınız!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre!', 'error')
    
    return render_template('login.html')

# Çıkış
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız!', 'success')
    return redirect(url_for('index'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Son 24 saatteki verileri al
    from datetime import timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    veriler = (
        IsiVerisi.query
        .filter(IsiVerisi.timestamp >= yesterday)
        .order_by(IsiVerisi.id.desc())
        .limit(50)
        .all()
    )
    
    # İstatistikler
    toplam_veri = IsiVerisi.query.count()
    ortalama_sicaklik = db.session.query(db.func.avg(IsiVerisi.sicaklik)).scalar() or 0
    max_sicaklik = db.session.query(db.func.max(IsiVerisi.sicaklik)).scalar() or 0
    min_sicaklik = db.session.query(db.func.min(IsiVerisi.sicaklik)).scalar() or 0
    
    return render_template('dashboard.html', 
                         veriler=veriler, 
                         toplam_veri=toplam_veri,
                         ortalama_sicaklik=round(ortalama_sicaklik, 2),
                         max_sicaklik=round(max_sicaklik, 2),
                         min_sicaklik=round(min_sicaklik, 2))

# Admin paneli
@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    bildirim_ayarlari = BildirimAyarlari.query.first()
    if not bildirim_ayarlari:
        bildirim_ayarlari = BildirimAyarlari(admin_email='admin@example.com')
        db.session.add(bildirim_ayarlari)
        db.session.commit()
    
    return render_template('admin.html', users=users, ayarlar=bildirim_ayarlari)

# Kullanıcı ekleme
@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'})
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Bu kullanıcı adı zaten kullanılıyor'})
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Kullanıcı başarıyla eklendi'})

# Bildirim ayarlarını güncelleme
@app.route('/admin/update_settings', methods=['POST'])
@login_required
def update_settings():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'})
    
    max_sicaklik = float(request.form['max_sicaklik'])
    email_bildirim = 'email_bildirim' in request.form
    admin_email = request.form['admin_email']
    email_ofis = request.form.get('email_ofis', '').strip()
    email_depo = request.form.get('email_depo', '').strip()
    email_laboratuvar = request.form.get('email_laboratuvar', '').strip()
    smtp_server = request.form.get('smtp_server', 'smtp.gmail.com').strip()
    smtp_port = int(request.form.get('smtp_port', 587))
    smtp_email = request.form.get('smtp_email', '').strip()
    smtp_password = request.form.get('smtp_password', '').strip()
    
    ayarlar = BildirimAyarlari.query.first()
    if not ayarlar:
        ayarlar = BildirimAyarlari()
        db.session.add(ayarlar)
    
    ayarlar.max_sicaklik = max_sicaklik
    ayarlar.email_bildirim = email_bildirim
    ayarlar.admin_email = admin_email
    ayarlar.email_ofis = email_ofis
    ayarlar.email_depo = email_depo
    ayarlar.email_laboratuvar = email_laboratuvar
    ayarlar.smtp_server = smtp_server
    ayarlar.smtp_port = smtp_port
    ayarlar.smtp_email = smtp_email
    ayarlar.smtp_password = smtp_password
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Ayarlar güncellendi'})

# Test e-posta gönderimi
@app.route('/admin/test_email', methods=['POST'])
@login_required
def test_email():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'})
    ayarlar = BildirimAyarlari.query.first()
    if not ayarlar or not ayarlar.admin_email:
        return jsonify({'success': False, 'message': 'Admin e-posta adresi tanımlı değil'})
    ok = send_email_notification('Test Mail - Isı Takip Sistemi', 'Bu bir test e-postasıdır.', ayarlar.admin_email)
    return jsonify({'success': ok, 'message': 'Test e-postası gönderildi' if ok else 'E-posta gönderilemedi'})

# API - Yeni ısı verisi ekleme
@app.route('/api/add_data', methods=['POST'])
def add_data():
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        sicaklik = float(data.get('sicaklik'))
        nem = float(data.get('nem'))
        lokasyon = data.get('lokasyon', 'Bilinmeyen')
        
        yeni_veri = IsiVerisi(
            sensor_id=sensor_id,
            sicaklik=sicaklik,
            nem=nem,
            lokasyon=lokasyon
        )
        db.session.add(yeni_veri)
        db.session.commit()
        
        # Yüksek sıcaklık kontrolü
        ayarlar = BildirimAyarlari.query.first()
        if ayarlar and ayarlar.email_bildirim and sicaklik > ayarlar.max_sicaklik:
            subject = f"Sıcaklık Fazla Yüksek - {lokasyon}"
            tr_now = (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
            message = (
                "Sistem Uyarısı: Sıcaklık eşiği aşıldı.\n\n"
                f"Lokasyon: {lokasyon}\n"
                f"Sensör: {sensor_id}\n"
                f"Sıcaklık: {sicaklik}°C (Eşik: {ayarlar.max_sicaklik}°C)\n"
                f"Nem: {nem}%\n"
                f"Zaman (UTC+3): {tr_now}\n"
            )

            # Alıcıları lokasyona göre belirle
            recipients = set()
            if ayarlar.admin_email:
                recipients.add(ayarlar.admin_email)
            lokasyon_lower = (lokasyon or '').lower()
            if ('ofis a' in lokasyon_lower) or ('ofis b' in lokasyon_lower) or ('ofis' in lokasyon_lower):
                if getattr(ayarlar, 'email_ofis', None):
                    recipients.add(ayarlar.email_ofis)
            elif 'depo' in lokasyon_lower:
                if getattr(ayarlar, 'email_depo', None):
                    recipients.add(ayarlar.email_depo)
            elif 'laboratuvar' in lokasyon_lower or 'laboratuar' in lokasyon_lower:
                if getattr(ayarlar, 'email_laboratuvar', None):
                    recipients.add(ayarlar.email_laboratuvar)

            for to_email in recipients:
                send_email_notification(subject, message, to_email)
        
        return jsonify({'success': True, 'message': 'Veri başarıyla eklendi'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Veri listesi API
@app.route('/api/data')
@login_required
def get_data():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    veriler = IsiVerisi.query.order_by(IsiVerisi.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    data = []
    for veri in veriler.items:
        data.append({
            'id': veri.id,
            'sensor_id': veri.sensor_id,
            'sicaklik': veri.sicaklik,
            'nem': veri.nem,
            'lokasyon': veri.lokasyon,
            'timestamp': (veri.timestamp + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'data': data,
        'total': veriler.total,
        'pages': veriler.pages,
        'current_page': page
    })

def init_db_and_seed():
    with app.app_context():
        db.create_all()
        # Basit şema yükseltmesi: yeni sütunları yoksa ekle
        try:
            existing_cols = {r[1] for r in db.session.execute(db.text("PRAGMA table_info('bildirim_ayarlari')")).fetchall()}
            alter_stmts = []
            if 'email_ofis' not in existing_cols:
                alter_stmts.append("ALTER TABLE bildirim_ayarlari ADD COLUMN email_ofis VARCHAR(120)")
            if 'email_depo' not in existing_cols:
                alter_stmts.append("ALTER TABLE bildirim_ayarlari ADD COLUMN email_depo VARCHAR(120)")
            if 'email_laboratuvar' not in existing_cols:
                alter_stmts.append("ALTER TABLE bildirim_ayarlari ADD COLUMN email_laboratuvar VARCHAR(120)")
            if 'smtp_server' not in existing_cols:
                alter_stmts.append("ALTER TABLE bildirim_ayarlari ADD COLUMN smtp_server VARCHAR(120)")
            if 'smtp_port' not in existing_cols:
                alter_stmts.append("ALTER TABLE bildirim_ayarlari ADD COLUMN smtp_port INTEGER")
            if 'smtp_email' not in existing_cols:
                alter_stmts.append("ALTER TABLE bildirim_ayarlari ADD COLUMN smtp_email VARCHAR(120)")
            if 'smtp_password' not in existing_cols:
                alter_stmts.append("ALTER TABLE bildirim_ayarlari ADD COLUMN smtp_password VARCHAR(255)")
            for stmt in alter_stmts:
                db.session.execute(db.text(stmt))
            if alter_stmts:
                db.session.commit()
        except Exception as e:
            print(f"Şema kontrolü sırasında hata: {e}")

        # İlk admin kullanıcısını oluştur
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin kullanıcısı oluşturuldu: admin/admin123")

        # Test user kullanıcısını oluştur
        if not User.query.filter_by(username='user').first():
            user = User(
                username='user',
                email='user@example.com',
                password_hash=generate_password_hash('user123'),
                role='user'
            )
            db.session.add(user)
            db.session.commit()
            print("User kullanıcısı oluşturuldu: user/user123")


# Uygulama yüklendiğinde (prod dahil) veritabanını hazırla
init_db_and_seed()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
