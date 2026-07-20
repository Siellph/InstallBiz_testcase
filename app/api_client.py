import io
import time
import zipfile

import requests


class ExternalApiClient:
    def __init__(self, base_url: str, candidate_id: str = None, timeout: int = 30, status_callback=None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.status_callback = status_callback
        self.session = requests.Session()
        if candidate_id:
            self.session.headers['X-Candidate-Id'] = candidate_id

    def _request(self, method: str, path: str, **kwargs):
        '''
        Выполняет запрос с учетом ограничений API:
        - 429 Too Many Requests -> ожидание из Retry-After + запас и повтор;
        - 403 Forbidden -> читаем текст из detail, ожидание с запасом.
        '''
        url = f'{self.base_url}{path}'
        while True:
            resp = self.session.request(method, url, timeout=self.timeout, **kwargs)

            if resp.status_code in (429, 403):
                retry_after = int(resp.headers.get('Retry-After', '30')) + 2

                server_message = ''
                try:
                    server_message = resp.json().get('detail', '')
                except Exception:
                    pass

                if not server_message:
                    server_message = (
                        'Доступ временно заблокирован (403).'
                        if resp.status_code == 403
                        else 'Превышена частота запросов (429).'
                    )

                for remaining in range(retry_after, 0, -1):
                    if self.status_callback:
                        mins = remaining // 60
                        secs = remaining % 60

                        if mins > 0:
                            time_str = f'{mins} мин {secs} сек'
                        else:
                            time_str = f'{secs} сек'

                        self.status_callback(f'{server_message.split('.')[0]}. Блокировка будет снята через {time_str}')
                    time.sleep(1)

                continue

            resp.raise_for_status()
            return resp

    def get_names(self) -> list:
        '''GET /api/files/names — возвращает список строк-имен (извлекает из ключа file_names).'''
        resp = self._request('GET', '/api/files/names')
        return resp.json().get('file_names', [])

    def download_batch(self, names: list) -> dict:
        if len(names) > 3:
            raise ValueError('За один запрос можно скачать не более 3 файлов')

        resp = self._request('POST', '/api/files/download', json={'file_names': names})

        result = {}
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for entry in zf.namelist():
                with zf.open(entry) as f:
                    result[entry] = f.read().decode('utf-8').strip()
        return result

    def mark_downloaded(self, names: list):
        if not names:
            return
        self._request('POST', '/api/files/downloaded', json={'file_names': names})
