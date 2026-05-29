# Gold API Deployment

Target path on server:

```bash
/opt/gold/backend
```

Service:

```bash
gold-api.service
```

Initial server setup outline:

```bash
sudo apt update
sudo apt install -y python3 python3-venv nginx rsync
sudo useradd --system --create-home --shell /usr/sbin/nologin gold || true
sudo mkdir -p /opt/gold
sudo chown -R gold:gold /opt/gold
```

After uploading backend files:

```bash
cd /opt/gold/backend
sudo -u gold python3 -m venv .venv
sudo -u gold .venv/bin/pip install -r requirements.txt
sudo install -m 0644 /opt/gold/deploy/gold-api.service /etc/systemd/system/gold-api.service
sudo install -m 0644 /opt/gold/deploy/nginx-gold-api.conf /etc/nginx/sites-available/gold-api
sudo ln -sf /etc/nginx/sites-available/gold-api /etc/nginx/sites-enabled/gold-api
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now gold-api
sudo systemctl reload nginx
```
