# YoutubeVideoDownloader

[![Build Windows](https://github.com/medneem/YoutubeVideoDownloader/actions/workflows/build-windows.yml/badge.svg)](https://github.com/medneem/YoutubeVideoDownloader/actions/workflows/build-windows.yml)

**YoutubeVideoDownloader** — бесплатная портативная программа с русским интерфейсом для скачивания видео и аудио с YouTube на Windows 10/11 (x64). Без рекламы, подписки и обязательной установки Python.

> Статус: ранняя версия (MVP). Независимый проект, не связанный с YouTube или Google.

## Возможности

- Скачивание отдельных видео через yt-dlp, выбор разрешения вплоть до 2160p/4K (при наличии исходного формата).
- Видео MP4 или извлечение аудиодорожки в MP3 (192 кбит/с).
- Выбор папки для загрузки, индикация прогресса, скорости, времени и кнопка отмены.
- Русский интерфейс и окно **⚙ Настройки** с HTTP/HTTPS-прокси.
- Все настройки в **config.json рядом с EXE**; перенос программы вместе с настройками.
- Версия в окне приложения, свойствах Windows EXE, названии ZIP и GitHub Releases соответствует номеру GitHub Actions pipeline.

Плейлисты, параллельные загрузки и субтитры планируются на будущее.

## Скачать

Самые свежие стабильные результаты успешных сборок находятся в [**GitHub Releases**](https://github.com/medneem/YoutubeVideoDownloader/releases).

1. Откройте Releases и выберите последнюю версию (например, `v0.1.42`).
2. В разделе **Assets** скачайте `YoutubeVideoDownloader-v0.1.42-windows-x64.zip` (номер версии будет своим).
3. Распакуйте **всю папку** из архива и запустите `YoutubeVideoDownloader.exe`.

Внутри архива находятся приложение, Python-библиотеки в `_internal/`, `ffmpeg.exe`, `ffprobe.exe`, `deno.exe` и `VERSION.txt`. **Переносите всю папку**, а не отдельный EXE. Программа не подписана цифровой подписью; SmartScreen может показать предупреждение.

Каждая сборка также доступна в [**Actions → Build Windows → Artifacts**](https://github.com/medneem/YoutubeVideoDownloader/actions/workflows/build-windows.yml), даже для pull request. Артефакты хранятся **14 дней** и требуют авторизации на GitHub для скачивания. Релизы остаются доступны и после истечения этого срока.

## Настройки и HTTP-прокси

**По умолчанию HTTP-прокси выключен.** Приложение обращается к YouTube напрямую, пока пользователь сам не включит прокси.

При первом запуске рядом с `YoutubeVideoDownloader.exe` автоматически создаётся `config.json`:

```json
{
  "download_dir": "C:\\Users\\User\\Downloads",
  "mode": "video",
  "quality": "best",
  "proxy_enabled": false,
  "proxy_url": ""
}
```

Для включения нажмите **⚙ Настройки**, отметьте **Использовать HTTP-прокси**, укажите URL в формате `http://127.0.0.1:8118` и сохраните. HTTP/HTTPS-прокси передаётся в yt-dlp для следующих загрузок. Чтобы снова скачивать напрямую, снимите галочку.

Параметры сохраняются автоматически при изменении. Если вы переносите программу на другой компьютер, перенесите всю папку вместе с `config.json`.

> Каталог приложения должен быть доступен на запись. Не рекомендуется размещать портативную версию в защищённом `Program Files`. Данные аутентификации, встроенные в адрес прокси, будут записаны в `config.json` открытым текстом. Не публикуйте этот файл.

## Нумерация версий и автоматические Releases

У проекта используется схема `vMAJOR.MINOR.PIPELINE`. Базовая версия задаётся в [workflow](.github/workflows/build-windows.yml) через `BASE_VERSION: "0.1"`, а `PIPELINE` — встроенный номер запуска `github.run_number`.

Пример для pipeline **#42**:

| Где | Значение |
| --- | --- |
| Версия приложения | `0.1.42` |
| Git tag и Release | `v0.1.42` |
| Готовый ZIP | `YoutubeVideoDownloader-v0.1.42-windows-x64.zip` |
| Windows EXE FileVersion | `0.1.42.0` |
| Файл VERSION.txt | `0.1.42` |

Номер запуска уникален внутри этого workflow; возможны пропуски из-за pull request и неудачных сборок. **Номер pipeline не означает число опубликованных релизов.** При повторном запуске того же workflow сохраняется номер версии, а ZIP-ресурс существующего релиза может обновиться.

### Pipeline

Workflow автоматически запускается при push в `main`, при pull request и вручную.

**Job 1 — Windows x64 portable ZIP:**

1. Устанавливает Python 3.13, PySide6, yt-dlp, PyInstaller.
2. Генерирует `version.py` и ресурс Windows EXE (`windows_version_info.txt`) из номера запуска.
3. Запускает тесты.
4. Собирает папку программы через PyInstaller.
5. Добавляет FFmpeg, FFprobe, Deno, файлы лицензий и `VERSION.txt`.
6. Проверяет обязательные файлы, создаёт ZIP и сохраняет его в Actions → Artifacts. Отсутствующий ZIP приводит к **ошибке сборки**, а не к зелёному pipeline.

**Job 2 — Publish GitHub Release:**

- Запускается **только после успешного первого job** для push в `main` или ручного запуска на `main`.
- Получает уже собранный ZIP из Actions, создаёт тег `v0.1.<номер запуска>` и GitHub Release, прикладывая ZIP в **Assets**.
- Не публикует релизы из pull request.
- При повторном запуске того же pipeline обновляет ZIP-ресурс существующего релиза.

Успешный полный pipeline на `main` означает, что ZIP опубликован **и как Artifacts, и как GitHub Release**. Сборка не выполняет реальную интеграционную загрузку с YouTube, поэтому работу на конкретном компьютере стоит проверить вручную.

## Локальная разработка

Технологии: **Python 3.13, PySide6, yt-dlp[default], FFmpeg, Deno, PyInstaller, GitHub Actions**.

Установите Python 3.13 и выполните в PowerShell:

```powershell
git clone https://github.com/medneem/YoutubeVideoDownloader.git
cd YoutubeVideoDownloader
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-build.txt
python main.py
```

Для локальной загрузки нужны `ffmpeg` и `deno` в `PATH` или исполняемые файлы рядом с `main.py`.

```powershell
python -m unittest discover -s tests -v
```

При запуске исходников версия — `0.1.0-dev`, а CI автоматически подменяет её. Для ручной проверки генерации версии:

```powershell
python scripts/stamp_version.py 0.1 42
```

Генерируемый `windows_version_info.txt` игнорируется Git. После этой команды `version.py` локально изменён; перед новым коммитом восстановите `version.py`, если не хотите коммитить локальный номер.

## Структура

```text
.github/workflows/build-windows.yml  # CI, Artifacts и Releases
scripts/stamp_version.py             # версия от github.run_number
version.py                           # версия для разработки / генерация в CI
main.py                              # окно программы, текущая версия, HTTP-прокси
settings.py                          # config.json рядом с EXE
downloader.py                        # yt-dlp, FFmpeg, Deno, поток загрузки
tests/                               # автоматические тесты
requirements.txt                     # зависимости
requirements-build.txt               # PyInstaller и зависимости
THIRD_PARTY_NOTICES.md               # уведомления о сторонних компонентах
LICENSE                              # MIT
README.md
```

## Планы

- [x] Портативная Windows-версия, русское GUI, HTTP-прокси и config.json.
- [x] Автоматическая нумерация по pipeline, ZIP в Artifacts и GitHub Releases.
- [ ] Очередь, плейлисты и несколько одновременных загрузок.
- [ ] Субтитры, обложки, метаданные и дополнительные форматы.
- [ ] Обновление yt-dlp, отдельный установщик и цифровая подпись.

## Лицензия и ответственность

Исходный код приложения распространяется по [MIT](LICENSE); сторонние инструменты и библиотеки — по собственным лицензиям. См. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). При распространении бинарных сборок необходимо выполнять условия лицензий FFmpeg, Qt и других компонентов, включая требования по уведомлениям и исходным кодам, где они применимы.

Скачивайте только материалы, на использование которых у вас есть необходимые права, соблюдая правила платформы и законодательство.
