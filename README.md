در ادامه **گزارش کامل و نهایی اجرای پروژه Docker Compose برای استک Flask + Nginx (با HTTPS و مانیتورینگ Prometheus/Grafana)** آورده شده است. این گزارش تمام مراحل، تصمیم‌ها، خطاها و وضعیت نهایی را پوشش می‌دهد 👇  

---

## 🧩 خلاصه‌ی کلی پروژه

کاربر درخواست ساخت یک استک کامل شامل سرویس **Hello World (Flask)**، **Nginx Reverse Proxy با HTTPS self-signed** و **سیستم مانیتورینگ Prometheus + Grafana** کرد؛ هدف اجرای همه‌ی سرویس‌ها به‌صورت محلی روی **localhost با Docker Compose** بود.

---

## 🚀 مراحل اجرایی پروژه

### 1. تأیید محیط
تأیید شد که محیط ‌هدف، **localhost** با نصب Docker و docker-compose است.

---

### 2. طراحی اولیه استک
استک شامل سرویس‌های زیر بود:

| سرویس | نقش |
|-------|------|
| `app` | اپلیکیشن Flask (Hello World) |
| `nginx` | Reverse Proxy با HTTPS و اتصال به Flask |
| `nginx_exporter` | جمع‌آوری متریک‌های Nginx |
| `prometheus` | پایش متریک‌ها |
| `grafana` | مصورسازی و ساخت داشبورد |

ساختار فایل‌ها شامل:
- `app/Dockerfile` و `app/app.py`  
- `nginx/nginx.conf` و `nginx/ssl/server.crt`, `server.key`  
- `monitoring/prometheus.yml`  
- ریشه پروژه: `docker-compose.yaml`

---

### 3. تولید گواهی SSL Self-signed
با دستور زیر انجام شد:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt
```
فایل‌ها در مسیر `nginx/ssl/` قرار گرفتند.

---

### 4. مانیتورینگ Flask
در اپ Flask از کتابخانه‌ی `prometheus_flask_exporter` استفاده شد تا متریک‌ها روی `/metrics` در پورت `5000` منتشر شوند.

نمونه متریک‌ها:
- `flask_http_request_duration_seconds_sum`
- `flask_http_request_duration_seconds_count`

---

### 5. مانیتورینگ Nginx
با استفاده از **nginx-prometheus-exporter** و فعال کردن `stub_status` روی پورت 8080 در تنظیمات Nginx:

```nginx
server {
    listen 8080;
    server_name localhost;

    location /stub_status {
        stub_status;
        allow all;
    }
}
```

این مسیر بعدها توسط Exporter خوانده شد:
```
--nginx.scrape-uri=http://nginx_proxy:8080/stub_status
```

---

### 6. پیکربندی کامل Nginx
```nginx
events {}

http {
    server {
        listen 443 ssl;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;

        location / {
            proxy_pass http://app:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    server {
        listen 8080;
        server_name localhost;

        location /stub_status {
            stub_status;
            allow all;
        }
    }
}
```

---

### 7. آرایش Docker Compose
فایل `docker-compose.yaml` شامل همه‌ی سرویس‌ها و اتصال‌ها بود:

```yaml
version: "3"

services:
  app:
    build: ./app
    container_name: hello_app
    expose:
      - "5000"

  nginx:
    build: ./nginx
    container_name: nginx_proxy
    ports:
      - "443:443"
    depends_on:
      - app

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

  nginx_exporter:
    image: nginx/nginx-prometheus-exporter:latest
    command:
      - '--nginx.scrape-uri=http://nginx_proxy:8080/stub_status'
    ports:
      - "9113:9113"
    depends_on:
      - nginx
```

---

### 8. رفع خطاهای اجرای اولیه
در طول اجرا چند خطا رفع شد:

| شماره | نوع خطا | علت | راه‌حل |
|-------|----------|------|--------|
| ۱ | پیدا نشدن `server.crt`/`server.key` | مسیر اشتباه یا فایل ناموجود | ساخت و قرار دادن فایل در `nginx/ssl/` ✅ |
| ۲ | خطای Mount پرومتئوس | به‌جای فایل، پوشه‌ای به نام `prometheus.yml` ساخته شده بود | حذف پوشه و ساخت فایل واقعی ✅ |
| ۳ | خطا در پارامتر exporter | استفاده از یک خط تیره به‌جای دو (`-nginx.scrape-uri` به‌جای `--nginx.scrape-uri`) | اصلاح ✅ |
| ۴ | هشدار version قدیمی Compose (`3.8`) | هشدار بی‌خطر، قابل‌چشم‌پوشی ✅ |

---

### 9. اجرای موفق
پس از رفع خطاها:
```bash
docker compose up -d
```
همه‌ی سرویس‌ها بدون مشکل اجرا شدند.

---

### 10. تست نهایی
- ✅ دسترسی موفق به **`https://localhost`** (با هشدار امنیتی SSL خودامضا)
- ✅ وضعیت **UP** برای تارگت‌های Prometheus (`flask_app` و `nginx_exporter`)
- ✅ ورود به Grafana با نام کاربری `admin` / `admin`

---

### 11. ساخت داشبورد Grafana
در داخل Grafana:
- Data Source = `http://prometheus:9090`
- مثال از کوئری محاسبه Latency:
  ```promql
  rate(flask_http_request_duration_seconds_sum[5m])
  /
  rate(flask_http_request_duration_seconds_count[5m])
  ```
- پنل‌ها:
  - میانگین زمان پاسخ Flask
  - تعداد درخواست‌های موفق
  - وضعیت Nginx از طریق Exporter

---

### 12. انتقال به Kubernetes (پیشنهاد بعدی)
در مرحله بعد، نقشهٔ مهاجرت داده شد:
- تبدیل هر سرویس به **Deployment**
- ایجاد **Service** برای ارتباط داخلی
- استفاده از **Secret** برای SSL key و cert
- ساخت **ConfigMap** برای فایل Prometheus

---

## ✅ وضعیت نهایی

| مولفه | وضعیت |
|--------|--------|
| Flask سرویس | اجرا و پاسخ موفق |
| HTTPS (Nginx) | فعال با SSL self-signed |
| Prometheus | تارگت‌ها شناسایی‌شده و UP |
| Grafana | تنظیم و کارآمد |
| Exporter | متریک‌ها قابل‌دسترسی |
| استک کلی | پایدار، بدون خطا |

---

## 📘 نتیجه و جمع‌بندی

پروژه با موفقیت کامل پیاده‌سازی شد؛ همه اجزای استک شامل **فلَسک، پروکسی HTTPS، Prometheus و Grafana** به شکل پایدار روی محیط محلی اجرا شدند.  
در نهایت مستندسازی پروژه (`README.md`) و طرح ادامه‌دار برای مهاجرت به Kubernetes نیز ارائه شد.

