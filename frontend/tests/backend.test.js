import test from 'node:test';
import assert from 'node:assert/strict';
import { toDataset } from '../src/lib/backend.js';

function response(flags, status = 'found') {
  return {
    lang: 'en', patient: { id: 'independent-example' }, prompt: 'Review', plan: { nodes: [] },
    documents: [{ id: 'example', date: '2024-01-01', sections: [{ paragraphs: [
      flags.map((flag) => ({ id: flag.segment_id, text: flag.text })),
    ] }] }],
    result: {
      patient: { as_of: '2024-01-01' }, items: [{ item_id: 'test', label: { en: 'Findings' },
        flags, status, priority: 'high', order: 0 }], custom: [], conflicts: [], derived: [],
      mode: 'partial', models: { check: 'gemini-test' }, issues: ['Dense search unavailable: quota'],
    },
  };
}

test('all retained passages and their complete answers survive the UI adapter', () => {
  const flags = Array.from({ length: 7 }, (_, i) => ({
    segment_id: `example#${i}`, doc_id: 'example', start: 0, doc_date: '2024-01-01',
    text: `Independent finding ${i}: ${'context '.repeat(35)}important concluding detail ${i}.`,
    keyword: 'Incomplete excerpt …', polarity: 'affirmed', current: true,
  }));
  const dataset = toDataset(response(flags));
  const row = dataset.encounter.important[0];
  for (const flag of flags) assert.ok(row.summary.includes(flag.text));
  assert.equal(row.sources.length, 7);
  assert.ok(row.sources.every(dataset.store.resolves));
  assert.equal(dataset.encounter.retrievalLimited, true);
});

test('structured medication schedules remain readable and older sources are dated without claiming replacement', () => {
  const flag = { segment_id: 'example#1', doc_id: 'example', start: 0,
    text: 'InventedDrug 2mg oral 1 0 0 0', keyword: 'InventedDrug 2 mg oral 1-0-0-0',
    structured: { kind: 'medication' }, polarity: 'affirmed', current: false, doc_date: '2020-02-03' };
  const row = toDataset(response([flag])).encounter.important[0];
  assert.ok(row.summary.includes(flag.keyword));
  assert.ok(row.summary.includes('document dated 03 Feb 2020'));
  assert.ok(!row.summary.includes('superseded'));
});

test('incomplete processing is not rendered as missing documentation', () => {
  const row = toDataset(response([], 'processing_incomplete')).encounter.important[0];
  assert.match(row.summary, /Not fully processed/);
  assert.doesNotMatch(row.summary, /Not documented/);
});
