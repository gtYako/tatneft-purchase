# Инструкция по запуску проекта на Linux

Проект запускается через Docker Compose. В контейнерах поднимаются:

- `db` - PostgreSQL 16, база данных проекта;
- `backend` - Django + Django REST Framework + Gunicorn;
- `frontend` - собранный React/Vite интерфейс, отдаваемый через Nginx;
- `nginx` - внешний reverse proxy, который принимает HTTP-запросы и направляет их во frontend или backend.

Основной файл запуска: `docker-compose.yml`.

## 1. Установка Docker на Linux

Команды ниже подходят для Ubuntu/Debian.

```bash
sudo apt update
sudo apt install -y ca-certificates curl git

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Проверить установку:

```bash
docker --version
docker compose version
```

Чтобы запускать Docker без `sudo`, можно добавить пользователя в группу `docker`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 2. Получение проекта из GitHub

```bash
cd /opt
sudo git clone https://github.com/gtYako/tatneft-purchase.git oil_procurement
sudo chown -R $USER:$USER /opt/oil_procurement
cd /opt/oil_procurement
```

Если репозиторий уже есть на сервере:

```bash
cd /opt/oil_procurement
git pull origin main
```

## 3. Переменные окружения

В `docker-compose.yml` уже прописаны основные переменные для Django и PostgreSQL. Для анализа цен через GigaChat используется переменная `GIGACHAT_AUTH_KEY`.

Создать файл `.env` в корне проекта:

```bash
cd /opt/oil_procurement
nano .env
```

Пример содержимого:

```env
GIGACHAT_AUTH_KEY=ваш_ключ_авторизации_gigachat
```

Если ключ не указать, проект запустится, но endpoint анализа цен через GigaChat будет возвращать ошибку настройки ключа. PDF-отчет при этом можно формировать без блока AI-анализа.

## 4. Первый запуск проекта

```bash
cd /opt/oil_procurement
docker compose up -d --build
```

Что произойдет при первом запуске:

- соберется backend-образ на Python 3.12;
- соберется frontend-образ: React/Vite сначала собирается через Node 20, затем отдается через Nginx;
- поднимется PostgreSQL;
- backend дождется готовности PostgreSQL;
- выполнятся миграции Django;
- выполнится `collectstatic`;
- если пользователей еще нет, загрузятся демо-данные через `seed_data`;
- внешний `nginx` начнет принимать запросы на порту `80`.

Открыть сайт:

```text
http://localhost
```

На сервере вместо `localhost` используется IP или домен:

```text
http://SERVER_IP
http://almetpt-tatneft.online
```

## 5. Проверка, что все контейнеры работают

```bash
docker compose ps
```

Ожидаемые контейнеры:

```text
oil_db
oil_backend
oil_frontend
oil_nginx
```

Посмотреть логи всех сервисов:

```bash
docker compose logs -f
```

Посмотреть логи только backend:

```bash
docker compose logs -f backend
```

Посмотреть логи nginx:

```bash
docker compose logs -f nginx
```

## 6. Подключение к базе данных через DBeaver

База данных проекта - PostgreSQL в контейнере `db`. Если проект запускается локально через Docker Compose, то для подключения из DBeaver контейнер базы должен быть запущен.

Запустить только базу данных:

```bash
cd /opt/oil_procurement
docker compose up -d db
```

Или запустить весь проект:

```bash
cd /opt/oil_procurement
docker compose up -d
```

Проверить, что контейнер PostgreSQL работает:

```bash
docker compose ps
```

Параметры подключения в DBeaver:

```text
Тип подключения: PostgreSQL
Host: localhost
Port: 5432
Database: oil_procurement
Username: oil_user
Password: oil_pass
```

В `docker-compose.yml` порт базы проброшен так:

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

Это значит, что DBeaver сможет подключиться к базе с той же машины, где запущен Docker. База не открыта наружу для всего интернета, что безопаснее для сервера.

Если база запущена на удаленном сервере, напрямую с домашнего компьютера она обычно не откроется. В этом случае нужен SSH-туннель:

```bash
ssh -L 5433:127.0.0.1:5432 yako@81.26.184.201
```

Пока это SSH-подключение открыто, в DBeaver нужно указать:

```text
Host: localhost
Port: 5433
Database: oil_procurement
Username: oil_user
Password: oil_pass
```

Здесь `5433` - локальный порт на компьютере, а `5432` - порт PostgreSQL внутри сервера. Если порт `5433` занят, можно выбрать другой, например `55432`.

## 7. Полезные команды управления

Остановить контейнеры без удаления данных:

```bash
docker compose stop
```

Запустить остановленные контейнеры:

```bash
docker compose start
```

Остановить и удалить контейнеры, но оставить данные PostgreSQL в Docker volume:

```bash
docker compose down
```

Пересобрать проект после изменений в коде:

```bash
docker compose up -d --build
```

Перезапустить только backend:

```bash
docker compose restart backend
```

Войти в контейнер backend:

```bash
docker compose exec backend sh
```

Выполнить миграции вручную:

```bash
docker compose exec backend python manage.py migrate
```

Собрать Django static вручную:

```bash
docker compose exec backend python manage.py collectstatic --noinput
```

Создать суперпользователя Django:

```bash
docker compose exec backend python manage.py createsuperuser
```

Открыть Django shell:

```bash
docker compose exec backend python manage.py shell
```

Заново загрузить демо-данные:

```bash
docker compose exec backend python manage.py seed_data
```

## 8. Команды для парсинга и мониторинга поставщиков

В проекте есть management-команды для работы с источниками поставщиков.

Загрузить стартовые источники парсинга:

```bash
docker compose exec backend python manage.py seed_parsing_sources
```

Запустить парсинг цен поставщиков вручную:

```bash
docker compose exec backend python manage.py parse_supplier_prices
```

Загрузить поисковые запросы для поиска поставщиков:

```bash
docker compose exec backend python manage.py seed_supplier_discovery_queries
```

Запустить поиск сайтов поставщиков:

```bash
docker compose exec backend python manage.py discover_supplier_sites
```

Импортировать найденных кандидатов в поставщики:

```bash
docker compose exec backend python manage.py import_supplier_candidates
```

## 9. Обновление проекта на сервере из GitHub

Перед обновлением полезно сохранить текущий коммит, чтобы можно было быстро откатиться:

```bash
cd /opt/oil_procurement
git rev-parse --short HEAD
```

Обновить код:

```bash
cd /opt/oil_procurement
git pull origin main
```

Если менялись зависимости, Dockerfile, docker-compose или frontend, лучше пересобрать контейнеры:

```bash
docker compose up -d --build
```

Если менялся только backend-код без зависимостей, можно перезапустить backend:

```bash
docker compose restart backend
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py collectstatic --noinput
```

Проверить результат:

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 nginx
```

## 10. Откат к предыдущему варианту

Посмотреть историю коммитов:

```bash
cd /opt/oil_procurement
git log --oneline --decorate -10
```

Откатиться к конкретному коммиту:

```bash
cd /opt/oil_procurement
git checkout НУЖНЫЙ_ХЕШ_КОММИТА
docker compose up -d --build
```

Вернуться обратно на актуальную ветку `main`:

```bash
cd /opt/oil_procurement
git checkout main
git pull origin main
docker compose up -d --build
```

Если нужно сделать постоянный откат через Git, лучше использовать `git revert`, чтобы создать новый коммит отмены:

```bash
cd /opt/oil_procurement
git revert ХЕШ_ПЛОХОГО_КОММИТА
git push origin main
```

После push в `main` сработает CI/CD.

## 11. Как работает CI/CD

CI/CD описан в файле `.github/workflows/deploy.yml`.

Сценарий такой:

1. Разработчик делает изменения в проекте.
2. Изменения коммитятся и отправляются в GitHub в ветку `main`.
3. GitHub Actions запускает workflow `Deploy to Production`.
4. Workflow подключается к серверу по SSH.
5. На сервере выполняется `git pull origin main`.
6. Если изменились зависимости, Dockerfile, `docker-compose.yml` или frontend, контейнеры пересобираются.
7. Если изменения небольшие, контейнеры просто перезапускаются.
8. После этого выполняются миграции и сбор static-файлов.

Команды локально для отправки изменений:

```bash
git status
git add .
git commit -m "Описание изменений"
git push origin main
```

Секреты SSH для деплоя хранятся в настройках GitHub-репозитория:

- `SSH_HOST` - IP или домен сервера;
- `SSH_USER` - пользователь Linux на сервере;
- `SSH_PRIVATE_KEY` - приватный SSH-ключ для подключения.

## 12. Полный сброс проекта

Эта команда удаляет контейнеры и volumes, включая базу данных PostgreSQL. Использовать только если точно нужно стереть данные.

```bash
docker compose down -v
docker compose up -d --build
```

После такого запуска база создастся заново, миграции выполнятся автоматически, а демо-данные загрузятся через `seed_data`, если пользователей еще нет.
