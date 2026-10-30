import json
import os
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest
from app import key_settings
from app.server import App, Server, make_handler


def test_local_settings_save_replace_and_reject_cross_origin(tmp_path, monkeypatch):
    monkeypatch.setattr(key_settings, 'CONFIG', tmp_path / '.env')
    for name in list(os.environ):
        if key_settings.KEY_NAME.fullmatch(name):
            monkeypatch.delenv(name)
    # Restore the complete environment after testing save_keys, which mutates it.
    monkeypatch.setattr(key_settings.os, 'environ', dict(os.environ))
    server = Server(('127.0.0.1', 0), make_handler(App(None, False)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/api/settings/keys'
    def save(keys, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        return urlopen(Request(url, data=json.dumps({'keys': keys}).encode(), headers=headers))
    try:
        with save(['test-primary', 'test-backup', 'test-primary']) as response:
            data = json.load(response)
            assert data == {'count': 2, 'restartRequired': False}
        with urlopen(url) as response:
            assert json.load(response) == {'count': 2}
        with save(['replacement']) as response:
            assert json.load(response)['count'] == 1
        assert 'test-backup' not in key_settings.CONFIG.read_text()
        for keys in ([], ['a', 'b', 'c', 'd'], ['bad\nkey'], ['quoted"key']):
            with pytest.raises(HTTPError) as exc:
                save(keys)
            assert exc.value.code == 400
        with pytest.raises(HTTPError) as exc:
            save(['external'], 'https://example.com')
        assert exc.value.code == 403
        assert 'external' not in key_settings.CONFIG.read_text()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
