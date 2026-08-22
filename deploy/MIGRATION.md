# Переезд Destiny Code на сервер Timeweb (getdestinycode.ru)

Полный перенос сайта с Render на выделенный сервер `72.56.33.164`, где уже
живёт БД PostgreSQL (база `kniga`) и соседний проект `chilly` (его не трогаем).

Схема: **nginx → uvicorn (127.0.0.1:8100) → FastAPI**, TLS через certbot,
БД по **localhost**. Мы зеркалим то, как устроен `chilly` (порт 8000 у него —
поэтому у нас 8100).

> Команды на сервере выполняет владелец (SSH-правку сервера мой ассистент делать
> не может). После каждого крупного шага можно попросить проверку снаружи.

---

## 0. DNS (сделать первым — нужно для TLS)

В панели reg.ru → DNS домена `getdestinycode.ru`:

| Тип | Имя | Значение |
|-----|-----|----------|
| A   | `@`   | `72.56.33.164` |
| A   | `www` | `72.56.33.164` |

Подождать распространения (обычно минуты, иногда дольше). Проверка:
`ping getdestinycode.ru` должен показать `72.56.33.164`.

---

## 1. Код и сборка на сервере

```bash
git clone https://github.com/GlebBogatov/Kniga.git /var/www/getdestinycode
cd /var/www/getdestinycode/backend
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt

cd /var/www/getdestinycode/frontend
npm ci
npm run build
mkdir -p /var/www/getdestinycode/backend/static
cp -r dist/* /var/www/getdestinycode/backend/static/
```
(Если `npm run build` падает по памяти — `NODE_OPTIONS=--max-old-space-size=768 npm run build`.)

---

## 2. Переменные окружения (секреты — только на сервере)

Создать `/var/www/getdestinycode/backend/.env`. Значения `<...>` подставить
своими (БД — тот же пароль `kniga`, но host `127.0.0.1` и без sslmode; ключ
Timeweb и Яндекс — те же, что в Render):

```bash
cat > /var/www/getdestinycode/backend/.env <<'EOF'
DATABASE_URL=postgresql://kniga:<DB_PASS>@127.0.0.1:5432/kniga
LLM_PROVIDER=timeweb
TIMEWEB_BASE_URL=https://api.timeweb.ai/v1
TIMEWEB_API_KEY=<sk-...>
MODEL_INTERPRETATION=anthropic/claude-sonnet-5
MODEL_LIGHT=anthropic/claude-haiku-4-5
PUBLIC_BASE_URL=https://getdestinycode.ru
YANDEX_CLIENT_ID=<yandex_client_id>
YANDEX_CLIENT_SECRET=<yandex_client_secret>
ALLOW_DEV_LOGIN=true
FREEMIUM_ENABLED=true
CORS_ORIGINS=https://getdestinycode.ru
EOF
chmod 640 /var/www/getdestinycode/backend/.env
```

---

## 3. systemd-сервис (uvicorn на 127.0.0.1:8100)

```bash
cp /var/www/getdestinycode/deploy/destinycode.service /etc/systemd/system/
chown -R www-data:www-data /var/www/getdestinycode
systemctl daemon-reload
systemctl enable --now destinycode
systemctl status destinycode --no-pager
curl -s http://127.0.0.1:8100/api/health    # ждём {"status":"ok"}
```

---

## 4. nginx (server-блок getdestinycode.ru)

```bash
cp /var/www/getdestinycode/deploy/nginx-getdestinycode.conf /etc/nginx/sites-available/getdestinycode.ru
ln -s /etc/nginx/sites-available/getdestinycode.ru /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```
Теперь `http://getdestinycode.ru` уже должен открывать сайт (без HTTPS).

---

## 5. TLS (Let's Encrypt)

```bash
certbot --nginx -d getdestinycode.ru -d www.getdestinycode.ru
```
Certbot сам добавит блок :443 и редирект с :80. Проверка: `https://getdestinycode.ru`.

---

## 6. Яндекс OAuth — добавить redirect URI нового домена

В приложении на https://oauth.yandex.ru → добавить ещё один Redirect URI:
```
https://getdestinycode.ru/api/auth/oauth/yandex/callback
```
(старый onrender можно оставить или убрать). `PUBLIC_BASE_URL` уже указывает на
новый домен — вход пойдёт через него.

---

## 7. Проверка

- `https://getdestinycode.ru/` открывается, сертификат валиден;
- `https://getdestinycode.ru/api/health` → `{"status":"ok"}`;
- вход через Яндекс → возврат в кабинет на новом домене;
- гадание с реальным толкованием (ИИ через Timeweb) работает.

---

## 8. После успешного переезда

**Безопасность БД (теперь ходим по localhost — закрываем внешний доступ):**
```bash
# убрать внешнее правило и вернуть прослушивание только на localhost
sed -i '/hostssl kniga kniga/d' /etc/postgresql/14/main/pg_hba.conf
sed -i "s/^listen_addresses = '\*'/listen_addresses = 'localhost'/" /etc/postgresql/14/main/postgresql.conf
systemctl restart postgresql
ufw delete allow 5432/tcp 2>/dev/null || true
```
(После этого приложение подключается к БД по `127.0.0.1`, извне 5432 недоступен.)

**Render:** убедившись, что всё работает на новом хостинге, приостановить или
удалить сервис `kniga-peremen` (или оставить как запасной).

**Гигиена:** сменить пароль БД и root-пароль сервера (оба касались в переписке).

---

## Обновления сайта в дальнейшем

```bash
sudo bash /var/www/getdestinycode/deploy/deploy.sh
```
(git pull → пересборка фронта → зависимости → перезапуск сервиса.)
