"""Local-only Gemini configuration. Never return saved secret values."""
import os
import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / '.env'
KEY_NAME = re.compile(r'^(?:GEMINI|GOOGLE)[A-Z0-9_]*KEY[A-Z0-9_]*$|^API_KEY[_0-9]*$')


def save_keys(values):
    if not isinstance(values, list) or not 1 <= len(values) <= 3:
        raise ValueError('Enter one to three Gemini keys.')
    if any(not isinstance(v, str) or not v.strip() or len(v) > 256
           or any(c.isspace() for c in v.strip()) for v in values):
        raise ValueError('Enter keys without spaces, quotes, or variable names.')
    keys = list(dict.fromkeys(v.strip() for v in values))
    if any(not re.fullmatch(r'[A-Za-z0-9_.-]+', v) for v in keys):
        raise ValueError('Paste only the key values, without quotes or variable names.')
    lines = CONFIG.read_text(encoding='utf-8-sig').splitlines() if CONFIG.exists() else []
    lines = [s for s in lines if not KEY_NAME.fullmatch(s.partition('=')[0].strip())]
    entries = {('GEMINI_API_KEY' if i == 1 else f'GEMINI_API_KEY_{i}'): key
               for i, key in enumerate(keys, 1)}
    temporary = CONFIG.with_name('.env.tmp')
    try:
        temporary.write_text('\n'.join(lines + [f'{k}={v}' for k, v in entries.items()]) + '\n', encoding='utf-8')
        if os.name != 'nt':
            temporary.chmod(0o600)
        temporary.replace(CONFIG)
    finally:
        temporary.unlink(missing_ok=True)
    for name in list(os.environ):
        if KEY_NAME.fullmatch(name):
            del os.environ[name]
    os.environ.update(entries)
    os.environ['LLM_PROVIDER'] = 'gemini'
    return len(keys)
