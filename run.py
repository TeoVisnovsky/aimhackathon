"""Build and run the jury application: python run.py [--skip-setup] [--port 8000]."""
import argparse
import getpass
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def jury_environment(*, interactive=False, configure_keys=False):
    env = dict(os.environ)
    config = ROOT / 'backend/.env'
    if config.exists():
        for line in config.read_text(encoding='utf-8-sig').splitlines():
            key, separator, value = line.strip().partition('=')
            if separator and key and not key.startswith('#'):
                value = value.strip().strip('\"').strip("'")
                if value:
                    env.setdefault(key.strip(), value)
    if configure_keys:
        if not interactive:
            raise ValueError('Run python run.py in a terminal to paste the Gemini key, '
                             'or set GEMINI_API_KEY in your environment or backend/.env.')
        entered = getpass.getpass('Paste Gemini key(s), separated by commas (hidden): ')
        keys = list(dict.fromkeys(part.strip() for part in entered.split(',') if part.strip()))
        if not keys or any(any(character.isspace() for character in key) for key in keys):
            raise ValueError('Paste at least one key; separate multiple keys with commas, not spaces.')
        if len(keys) > 3:
            raise ValueError('Use at most three keys.')
        # Preserve unrelated settings; replace only the configured Gemini key list.
        names = re.compile(r'^GEMINI_API_KEY(?:_\d+)?$')
        lines = config.read_text(encoding='utf-8-sig').splitlines() if config.exists() else []
        lines = [line for line in lines if not names.fullmatch(line.partition('=')[0].strip())]
        for name in list(env):
            if names.fullmatch(name):
                env.pop(name)
        for index, key in enumerate(keys, start=1):
            name = 'GEMINI_API_KEY' if index == 1 else f'GEMINI_API_KEY_{index}'
            lines.append(name + '=' + key)
            env[name] = key
        config.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        if os.name != 'nt':
            config.chmod(0o600)
        print(f'{len(keys)} Gemini key(s) saved locally in backend/.env (excluded from Git).')
    for key in ('PATIENT_DIR', 'IMPORT_BUNDLE', 'HOST'):
        env.pop(key, None)
    env['ALLOW_IMPORT'] = '1'
    env['LLM_PROVIDER'] = 'gemini'
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-setup', action='store_true', help='Reuse installed dependencies and frontend build')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--configure-keys', action='store_true', help='Replace the saved Gemini key list')
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error('Python 3.12 or newer is required.')
    try:
        env = jury_environment(interactive=sys.stdin.isatty(), configure_keys=args.configure_keys)
    except ValueError as error:
        parser.error(str(error))
    python = ROOT / 'backend/.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not args.skip_setup:
        npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        if not npm:
            parser.error('Install Node.js 22 or newer (including npm), then run this command again.')
        if not python.exists():
            venv.create(python.parent.parent, with_pip=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', 'requirements-lock.txt',
                        '--disable-pip-version-check'], cwd=ROOT, check=True)
        subprocess.run([npm, 'ci', '--no-audit', '--no-fund'], cwd=ROOT / 'frontend', check=True)
        subprocess.run([npm, 'run', 'build'], cwd=ROOT / 'frontend', check=True)
    if not python.exists() or not (ROOT / 'frontend/dist/index.html').exists():
        parser.error('Setup is missing. Run python run.py without --skip-setup first.')
    print('Configure Gemini keys in the browser, then import the supplied patient folder.', flush=True)
    print(f'Open http://127.0.0.1:{args.port} and import the supplied patient folder. Ctrl+C stops the app.', flush=True)
    return subprocess.call([str(python), '-m', 'app.server', '--host', '127.0.0.1',
                            '--port', str(args.port), '--static', str(ROOT / 'frontend/dist')],
                           cwd=ROOT / 'backend', env=env)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as error:
        print('Setup failed. Check the error above, then rerun python run.py.', file=sys.stderr)
        raise SystemExit(error.returncode)
