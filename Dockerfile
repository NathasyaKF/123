sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

scp -r C:\Users\Lenovo\Desktop\new username@server-ip:/home/username/app

cd /home/username/app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

pip install gunicorn
gunicorn --bind 0.0.0.0:5000 log_summary_app:app

curl http://127.0.0.1:5000/summarize_logs

5. Setup Supervisor agar Aplikasi Tetap Berjalan

sudo nano /etc/supervisor/conf.d/log_summary_app.conf

[program:log_summary_app]
command=/home/username/app/venv/bin/gunicorn --bind 0.0.0.0:5000 log_summary_app:app
directory=/home/username/app
autostart=true
autorestart=true
stderr_logfile=/var/log/log_summary_app.err.log
stdout_logfile=/var/log/log_summary_app.out.log
Simpan (Ctrl + X, lalu Y, lalu Enter).

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start log_summary_app

sudo supervisorctl status

6. Konfigurasi Nginx sebagai Reverse Proxy

sudo nano /etc/nginx/sites-available/log_summary_app

server {
    listen 80;
    server_name yourdomain.com;  # Ganti dengan domain/IP server

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

sudo ln -s /etc/nginx/sites-available/log_summary_app /etc/nginx/sites-enabled/
sudo systemctl restart nginx

sudo systemctl status nginx
