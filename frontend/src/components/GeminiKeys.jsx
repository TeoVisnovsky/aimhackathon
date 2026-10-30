import { useEffect, useState } from 'react';

export function GeminiKeys() {
  const [keys, setKeys] = useState(['', '', '']);
  const [count, setCount] = useState(null);
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    fetch('/api/settings/keys').then(r => {
      if (!r.ok) throw new Error();
      return r.json();
    }).then(data => setCount(data.count)).catch(() => setMessage('Unable to read key settings.'));
  }, []);
  async function save() {
    setSaving(true);
    setMessage('');
    try {
      const response = await fetch('/api/settings/keys', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keys: keys.map(k => k.trim()).filter(Boolean) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not save keys.');
      setCount(data.count);
      setKeys(['', '', '']);
      setMessage(data.restartRequired
        ? 'Saved. A patient is already loaded: restart the app with python run.py --skip-setup to apply the new keys.'
        : 'Saved. You can now import the patient folder.');
    } catch (error) {
      setMessage(error.message || 'Could not save keys.');
    } finally { setSaving(false); }
  }
  return (
    <details className="login-key-settings" open={count === 0 ? true : undefined}>
      <summary>Gemini keys{count !== null ? ` · ${count} saved` : ''}</summary>
      <p className="login-import-note">Enter the keys from the submission form. One is sufficient; two backups are optional. Saved only on this computer. Saving replaces the previous list.</p>
      {keys.map((key, i) => (
        <label key={i} className="login-field">
          <span>{i === 0 ? 'Primary Gemini key' : `Backup ${i} (optional)`}</span>
          <input type="password" autoComplete="new-password" value={key}
            onChange={e => setKeys(previous => previous.map((v, n) => n === i ? e.target.value : v))} />
        </label>
      ))}
      <button type="button" onClick={save} disabled={saving || !keys[0].trim()}>
        {saving ? 'Saving…' : 'Save Gemini keys'}
      </button>
      <p className="login-import-note" role="status">{message}</p>
      <p className="login-import-note">Keys in the same Google project share quota.</p>
    </details>
  );
}
