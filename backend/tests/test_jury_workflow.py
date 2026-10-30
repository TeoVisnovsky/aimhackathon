"""Exercise the same HTTP routes used by the import-first jury build."""
import json
from pathlib import Path
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from app import importer, remarker
from app.server import App, Server, make_handler


def test_empty_start_import_assess_restart_and_static_boundary(tmp_path, monkeypatch):
    def no_cloud(*args, **kwargs):
        raise remarker.EmbeddingError('offline test')
    monkeypatch.setattr(remarker, 'GeminiEmbedder', no_cloud)
    monkeypatch.setattr(remarker, 'CACHE_DIR', tmp_path / 'index')
    monkeypatch.setattr(importer, 'IMPORT_DIR', tmp_path / 'imports')
    static = tmp_path / 'public'
    static.mkdir()
    (static / 'index.html').write_text('<h1>Import patient</h1>')
    (tmp_path / 'private.txt').write_text('private')
    app = App(None, use_llm=False)
    server = Server(('127.0.0.1', 0), make_handler(app, static))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'

    def post(path, body):
        request = Request(base + path, data=json.dumps(body).encode(),
                          headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    try:
        with urlopen(base + '/api/health') as response:
            assert json.load(response)['patients'] == 0
        with urlopen(base + '/') as response:
            assert b'Import patient' in response.read()
        for path in ('/%2e%2e/private.txt', '/api/unknown'):
            with pytest.raises(HTTPError) as error:
                urlopen(base + path)
            assert error.value.code == 404
        fixture = Path(__file__).parent / 'fixtures/patient-9999-0002'
        imported = post('/api/import', {'files': importer.files_from_folder(fixture)})
        assert imported['facts'] > 0 and imported['documents'] == 4
        result = post('/api/assess', {'task': 'Pulmonologist, COPD follow-up'})
        assert result['patient']['id'] == '9999-0002'
        assert result['result']['items'] and len(result['documents']) == 4
        again = App(None, use_llm=False)
        again.load_imports()
        assert again.find('', '') is not None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
