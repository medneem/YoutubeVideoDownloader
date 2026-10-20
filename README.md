# YoutubeVideoDownloader

[![Windows build](https://github.com/medneem/YoutubeVideoDownloader/actions/workflows/build-windows.yml/badge.svg)](https://github.com/medneem/YoutubeVideoDownloader/actions/workflows/build-windows.yml)
[![Latest release](https://img.shields.io/github/v/release/medneem/YoutubeVideoDownloader?label=release)](https://github.com/medneem/YoutubeVideoDownloader/releases/latest)

**YoutubeVideoDownloader** — бесплатная программа для Windows 10/11 x64 с русским интерфейсом для скачивания видео и аудио с YouTube. Не требует установки Python, не содержит рекламы и подписок.

> Проект независимый и не связан с Google или YouTube. Это ранняя версия (MVP).

## Скачать программу

**[Скачать последнюю версию в GitHub Releases](https://github.com/medneem/YoutubeVideoDownloader/releases/latest)**

1. Откройте последнюю версию в **Releases**.
2. В блоке **Assets** скачайте архив вида `YoutubeVideoDownloader-v0.1.N-windows-x64.zip`.
3. Создайте **новую пустую папку** и распакуйте в неё ZIP. Не распаковывайте поверх старой версии: Windows не удаляет оставшиеся от неё файлы, например `_internal`.
4. Запустите `YoutubeVideoDownloader.exe`.

Пример содержимого нового ZIP (файлы находятся **сразу в корне архива**, без дополнительной папки):

```text
YoutubeVideoDownloader.exe
ffmpeg.exe
ffprobe.exe
deno.exe
app-icon.png
VERSION.txt
LICENSE
THIRD_PARTY_NOTICES.md
```

**Это сборка `--onefile`:** Python, PySide6 и yt-dlp упакованы внутрь одного `YoutubeVideoDownloader.exe`. **Deno снова находится отдельно, рядом с EXE**, как и FFmpeg. Папки `_internal` в архиве **нет**. Если вы видите её в папке после обновления, скорее всего, это остаток старой версии `--onedir`: удалите старую папку и распакуйте новый ZIP в чистый каталог. При запуске PyInstaller временно распаковывает внутренние компоненты в системную временную папку; первый запуск может занимать больше времени, чем раньше.

**Важно:** `ffmpeg.exe`, `ffprobe.exe` и `deno.exe` должны оставаться рядом с программой — они намеренно вынесены за пределы основного EXE. Не удаляйте их.

Windows SmartScreen может предупреждать, что EXE пока не имеет цифровой подписи.

## Возможности

- Скачивание одного видео по ссылке.
- Загрузка видео с выбором максимального разрешения: автоматически, 2160p, 1440p, 1080p, 720p, 480p или 360p (если доступно у исходника).
- Извлечение аудио в MP3 (192 кбит/с).
- В имени файла указывается фактическое качество видео (например, `[1080p]`) либо формат и качество аудио (`[MP3 192kbps]`). Если файл с тем же именем уже есть, он заменяется при повторной загрузке.
- Выбор папки, прогресс, скорость, примерное оставшееся время и отмена загрузки.
- После успешной загрузки автоматически открывается папка в Проводнике; при ошибке или отмене не открывается.
- Собственная многоразмерная иконка: в заголовке окна, на панели задач и в свойствах EXE.
- Кнопка **«⚙ Настройки»** с HTTP/HTTPS-прокси и cookies YouTube (Chrome, Firefox, Edge или файл).
- Портативные настройки в `config.json` рядом с программой.
- Версия приложения и автоматическая публикация GitHub Releases по номеру pipeline.

Например, видео сохраняется как `Название [ID] [1080p].mp4`, а аудио — как `Название [ID] [MP3 192kbps].mp3`. Для режима «Максимальное» указывается реальное разрешение выбранного потока. Повторная загрузка **перезаписывает файл с тем же именем**, а не пропускает его и не продолжает прежнюю частичную загрузку. Файлы другого качества остаются на месте, поскольку имеют другое имя.

Плейлисты и параллельная загрузка нескольких видео пока не реализованы.

## Настройки: HTTP-прокси и cookies YouTube

При первом запуске рядом с `YoutubeVideoDownloader.exe` автоматически создаётся файл `config.json`. **По умолчанию прокси выключен.**

Пример содержимого:

```json
{
  "download_dir": "C:/Users/User/Downloads",
  "mode": "video",
  "quality": "best",
  "proxy_enabled": false,
  "proxy_url": "",
  "cookies_mode": "none",
  "cookies_browser": "chrome",
  "cookies_file": ""
}
```

Чтобы включить прокси:

1. Нажмите **⚙ Настройки**.
2. Отметьте **Использовать HTTP-прокси**.
3. Введите адрес, например `http://127.0.0.1:8118`.
4. Нажмите **Сохранить**.

Чтобы вернуться к прямому подключению, снимите флажок. Изменения сохраняются в `config.json` и применяются к следующим загрузкам.

### Cookies и авторизация YouTube

Если YouTube сообщает `Sign in to confirm you're not a bot`, откройте **⚙ Настройки → Авторизация YouTube (cookies)** и выберите один из режимов:

- **Без cookies** — по умолчанию; программа скачивает как раньше.
- **Cookies из браузера** — выберите Chrome, Firefox или Edge, в котором вы уже вошли в аккаунт YouTube. При ошибке чтения закройте браузер и повторите попытку.
- **Cookies из файла** — выберите локальный `cookies.txt` в формате Netscape (не JSON). Подходит, если браузер не отдаёт cookies автоматически.

Программа передаёт `yt-dlp` параметры `cookiesfrombrowser` или `cookiefile` только для активного режима. Режим, браузер и **путь** к файлу сохраняются в `config.json`; сами cookies программа в конфигурацию не копирует. Старый `config.json` без новых полей продолжает работать, cookies при этом выключены.

> Cookies являются конфиденциальными данными сессии. Не публикуйте `cookies.txt`, не отправляйте его третьим лицам и не добавляйте в Git. Экспортированные cookies могут перестать работать после выхода из аккаунта или истечения сессии. Авторизация не гарантирует скачивание всех видео.

Настройки сохраняются **возле самого EXE**, а не во временной папке распаковки PyInstaller. При обновлении достаточно заменить EXE и оставить старый `config.json`.

> Файл конфигурации должен быть доступен для записи. Не рекомендуется помещать портативную программу в защищённый `Program Files`. Если URL прокси содержит пароль, он хранится в `config.json` открытым текстом — не публикуйте этот файл.

## Автоматические сборки и версии

[**Windows pipeline**](https://github.com/medneem/YoutubeVideoDownloader/actions/workflows/build-windows.yml) запускается при push в `main`, при pull request и вручную.

Номер версии определяется так:

```text
Версия программы:  0.1.<номер workflow run>
Git-тег:           v0.1.<номер workflow run>
Имя ZIP:           YoutubeVideoDownloader-v0.1.<номер workflow run>-windows-x64.zip
```

Например, pipeline №42 создаст релиз `v0.1.42`. Базовую версию `0.1` задаёт `BASE_VERSION` в [workflow](.github/workflows/build-windows.yml).

**Процесс CI/CD:**

1. Установка зависимостей, генерация версии и запуск тестов.
2. Загрузка FFmpeg, FFprobe и Deno для Windows x64; создание многомасштабной иконки из `assets/app.svg`.
3. PyInstaller `--onefile`: только Python-зависимости, Qt и иконка встроены в EXE.
4. Проверка **содержимого готового ZIP**: ровно восемь файлов в корне архива, без вложенных директорий и `_internal`. При нарушении условия сборка завершается ошибкой.
5. Загрузка ZIP в **Actions → Artifacts**. Отсутствие архива завершает pipeline ошибкой.
6. После успешной сборки `main` автоматическое создание **GitHub Release**, куда добавляется **тот же ZIP**.

Для pull request ZIP создаётся только как артефакт — Release не публикуется. Artifacts хранятся 14 дней, релизы не ограничены этим сроком. Повторный запуск workflow использует тот же номер версии.

> Pipeline проверяет сборку и наличие файлов, но не тестирует фактическое скачивание с YouTube: доступность видео зависит от платформы, сети и выбранных форматов.

## Локальная разработка

**Стек:** Python 3.13, PySide6 (Qt), yt-dlp, Deno, FFmpeg, PyInstaller, GitHub Actions.

Для запуска исходников нужен Python 3.13. Исполняемые файлы `ffmpeg` и `deno` должны быть доступны в `PATH` или размещены рядом с `main.py`.

```powershell
git clone https://github.com/medneem/YoutubeVideoDownloader.git
cd YoutubeVideoDownloader
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-build.txt
python main.py
```

Тесты:

```powershell
python -m unittest discover -s tests -v
```

Для проверки генерации версии вручную:

```powershell
python scripts/stamp_version.py 0.1 42
```

В обычном режиме разработки версия `0.1.0-dev`; CI автоматически задаёт номер запуска. Команда выше изменяет локальный `version.py`, поэтому не включайте этот номер в коммит случайно.

## Структура репозитория

```text
.github/workflows/build-windows.yml   # CI, ZIP и GitHub Releases
scripts/stamp_version.py             # нумерация по pipeline
scripts/build_icon.py                 # конвертация SVG в ICO
assets/app.svg                        # исходник иконки
main.py                              # интерфейс PySide6
downloader.py                        # yt-dlp и поиск Deno/FFmpeg
settings.py                          # работа с config.json
version.py                           # версия приложения
tests/                               # тесты
requirements.txt                     # зависимости приложения
requirements-build.txt               # зависимости сборки
README.md                            # документация
```

## Планы

- [x] Портативная Windows-версия, русский интерфейс и HTTP-прокси.
- [x] `config.json` рядом с EXE, прокси и cookies выключены по умолчанию.
- [x] Поддержка cookies YouTube из браузера Chrome/Firefox/Edge и файла Netscape.
- [x] Сборка `--onefile` с внешними FFmpeg, FFprobe и Deno.
- [x] Новая иконка приложения и открытие папки после успешной загрузки.
- [x] GitHub Actions: ZIP в Artifacts и автоматические Releases.
- [ ] Очередь, плейлисты, параллельные загрузки.
- [ ] Субтитры, обложки, дополнительные кодеки и форматы.
- [ ] Автообновление yt-dlp, цифровая подпись, установщик.

## Лицензия

Код проекта распространяется по [MIT](LICENSE). Сторонние компоненты имеют собственные лицензии — см. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). При распространении бинарных файлов необходимо соблюдать применимые условия лицензий, в том числе FFmpeg и Qt.

Скачивайте только материалы, на получение и использование которых у вас есть права.
