import json

path = 'tmp/stash0_full.diff'
files = []
current = None
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.startswith('diff --git '):
            if current:
                files.append(current)
            parts = line.strip().split()
            a = parts[2][2:] if len(parts) >= 3 else ''
            b = parts[3][2:] if len(parts) >= 4 else ''
            current = {'path': b, 'a': a, 'b': b, 'lines': []}
        elif current is not None:
            current['lines'].append(line)
    if current:
        files.append(current)

out = []
for f in files:
    status = 'M'
    if any(l.startswith('new file mode') for l in f['lines']):
        status = 'A'
    if any(l.startswith('deleted file mode') for l in f['lines']):
        status = 'D'
    hunk_count = sum(1 for l in f['lines'] if l.startswith('@@ '))
    added = sum(1 for l in f['lines'] if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in f['lines'] if l.startswith('-') and not l.startswith('---'))
    sample = []
    for l in f['lines']:
        if l.startswith('@@ ') or l.startswith('+') or l.startswith('-'):
            sample.append(l.rstrip('\n'))
            if len(sample) >= 40:
                break
    out.append({'path': f['path'], 'status': status, 'hunks': hunk_count, 'added': added, 'removed': removed, 'sample': sample})

with open('tmp/stash0_parsed.json', 'w', encoding='utf-8') as out_f:
    json.dump(out, out_f, indent=2)

print('written', len(out))
