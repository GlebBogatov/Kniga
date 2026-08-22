#!/usr/bin/env bash
# Обновление уже развёрнутого сайта Destiny Code на сервере.
# Запуск: sudo bash /var/www/getdestinycode/deploy/deploy.sh
set -euo pipefail

APP=/var/www/getdestinycode
cd "$APP"

echo ">> git pull"
git pull --ff-only

echo ">> frontend build"
cd "$APP/frontend"
npm ci
npm run build
rm -rf "$APP/backend/static"
mkdir -p "$APP/backend/static"
cp -r dist/* "$APP/backend/static/"

echo ">> backend deps"
cd "$APP/backend"
.venv/bin/pip install -q -r requirements.txt

echo ">> права + перезапуск"
chown -R www-data:www-data "$APP"
systemctl restart destinycode
sleep 2
systemctl is-active destinycode
curl -sf http://127.0.0.1:8100/api/health && echo " OK"
