import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from app import storage
from app.api_client import ExternalApiClient

_lock = threading.Lock()

_state = {
    'status': 'idle',
    'started_at_nsk': None,
    'total_seen': 0,
    'downloaded': 0,
    'message': '',
}


def get_state() -> dict:
    with _lock:
        return dict(_state)


def _update(**kwargs):
    with _lock:
        _state.update(kwargs)


def start_download(base_url: str, candidate_id: str, tz_name: str) -> bool:
    '''Запускает фоновое скачивание. Возвращает False, если уже запущено.'''
    with _lock:
        if _state['status'] == 'running':
            return False
        _state.update(
            status='running',
            started_at_nsk=datetime.now(ZoneInfo(tz_name)).strftime('%Y-%m-%d %H:%M:%S'),
            total_seen=0,
            downloaded=0,
            message='Установление связи с API, запрос списка имён...',
        )

    thread = threading.Thread(target=_run, args=(base_url, candidate_id, tz_name), daemon=True)
    thread.start()
    return True


def _run(base_url: str, candidate_id: str, tz_name: str):
    def _status_updater(msg):
        _update(message=msg)

    client = ExternalApiClient(base_url, candidate_id or None, status_callback=_status_updater)

    seen = storage.get_known_names()
    downloaded_this_run = 0
    total_discovered_this_run = 0
    tz = ZoneInfo(tz_name)

    try:
        while True:
            _update(message='Запрос файлов...')
            names = client.get_names()
            time.sleep(1.5)

            if not names:
                break

            already_had = [n for n in names if n in seen]
            if already_had:
                try:
                    client.mark_downloaded(already_had)
                    time.sleep(1.5)
                except requests.exceptions.HTTPError as e:
                    if e.response is not None and e.response.status_code == 404:
                        for name in already_had:
                            try:
                                client.mark_downloaded([name])
                                time.sleep(1.0)
                            except requests.exceptions.HTTPError as se:
                                if se.response is not None and se.response.status_code == 404:
                                    pass
                                else:
                                    raise
                    else:
                        raise

            new_names = [n for n in names if n not in seen]

            if not new_names:
                _update(message='Полученные файлы уже скачаны ранее. Ожидание...')
                time.sleep(2)
                continue

            count = len(names)

            if count % 10 == 1 and count % 100 != 11:
                status_msg = f'Получен {count} файл. Загрузка...'
            elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
                status_msg = f'Получено {count} файла. Загрузка...'
            else:
                status_msg = f'Получено {count} файлов. Загрузка...'

            total_discovered_this_run += count
            _update(
                total_seen=total_discovered_this_run,
                message=status_msg,
            )

            for i in range(0, len(new_names), 3):
                batch = new_names[i : i + 3]
                if not batch:
                    continue

                now_str = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

                try:
                    content_map = client.download_batch(batch)
                    time.sleep(1.5)

                    if content_map:
                        client.mark_downloaded(list(content_map.keys()))
                        time.sleep(1.5)

                    for name, content in content_map.items():
                        storage.save_file(name, content, now_str)
                        seen.add(name)
                        downloaded_this_run += 1

                except requests.exceptions.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code == 404:
                        for name in batch:
                            try:
                                single_map = client.download_batch([name])
                                time.sleep(1.0)
                                for n, c in single_map.items():
                                    storage.save_file(n, c, now_str)
                                    seen.add(n)
                                    downloaded_this_run += 1
                                client.mark_downloaded([name])
                                time.sleep(1.0)
                            except requests.exceptions.HTTPError as single_exc:
                                if single_exc.response is not None and single_exc.response.status_code == 404:
                                    storage.save_file(name, '', now_str)
                                    seen.add(name)
                                    downloaded_this_run += 1
                                    try:
                                        client.mark_downloaded([name])
                                        time.sleep(1.0)
                                    except requests.exceptions.HTTPError as mark_exc:
                                        if mark_exc.response is not None and mark_exc.response.status_code == 404:
                                            pass
                                        else:
                                            raise
                                else:
                                    raise
                    else:
                        raise

                _update(downloaded=downloaded_this_run)

            time.sleep(1.5)

        _update(status='done', message='Каталог полностью скачан!')

    except requests.exceptions.HTTPError as exc:
        response = exc.response
        status_code = response.status_code if response is not None else 'Неизвестно'
        error_msg = f'Ошибка удаленного API ({status_code}): '

        try:
            err_json = response.json()
            detail = err_json.get('detail')

            if isinstance(detail, list):
                messages = []
                for err in detail:
                    loc = ' -> '.join(str(x) for x in err.get('loc', []))
                    msg = err.get('msg', 'Некорректное значение')
                    messages.append(f'[{loc}]: {msg}')
                error_msg += '; '.join(messages)

            elif isinstance(detail, str):
                error_msg += detail
            else:
                error_msg += response.text or response.reason
        except Exception:
            error_msg += response.reason if response is not None else str(exc)

        _update(status='error', message=error_msg)

    except requests.exceptions.RequestException as exc:
        _update(
            status='error',
            message=f'Сетевой сбой: Не удалось связаться с сервером API. Проверьте подключение. ({type(exc).__name__})',
        )

    except Exception as exc:
        _update(status='error', message=f'Внутренняя системная ошибка: {exc}')
