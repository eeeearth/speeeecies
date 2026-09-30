/* Live WebVTT overlay. The public feed path can be changed when its endpoint is approved. */
const feedBase = 'captions/live/';
const archiveBase = 'captions/archive/';
const trackSelect = document.querySelector('#caption-track');
const delayInput = document.querySelector('#caption-delay');
const status = document.querySelector('#caption-status');
const overlay = document.querySelector('#caption-overlay');
const archiveList = document.querySelector('#caption-archive');
let current = null;
let cues = [];

function seconds(clock) {
  const match = /^(\d\d):(\d\d):(\d\d)\.(\d\d\d)$/.exec(clock);
  if (!match) return NaN;
  return Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]) + Number(match[4]) / 1000;
}

function parseVtt(text) {
  const lines = text.split(/\r?\n/);
  const found = [];
  for (let i = 0; i < lines.length; i += 1) {
    const match = /^(\d\d:\d\d:\d\d\.\d\d\d) --> (\d\d:\d\d:\d\d\.\d\d\d)$/.exec(lines[i]);
    if (!match) continue;
    const start = seconds(match[1]);
    const end = seconds(match[2]);
    const body = [];
    while (i + 1 < lines.length && lines[i + 1].trim()) body.push(lines[++i]);
    if (Number.isFinite(start) && Number.isFinite(end)) found.push({ start, end, text: body.join(' ') });
  }
  return found;
}

function selectedTrack(manifest) {
  if (trackSelect.value !== 'spoken') return trackSelect.value;
  return manifest.tracks.find((track) => track !== 'en' && track !== 'tlh') || 'en';
}

function render() {
  if (!current || trackSelect.value === 'off') {
    if (overlay.textContent) overlay.textContent = '';
    return;
  }
  const delay = Math.min(120, Math.max(0, Number(delayInput.value) || 0));
  const elapsed = (Date.now() - current.start_epoch_ms) / 1000 - delay;
  const active = cues.filter((cue) => cue.start <= elapsed && elapsed < cue.end).at(-1);
  const nextText = active?.text || '';
  if (overlay.textContent !== nextText) overlay.textContent = nextText;
}

async function refresh() {
  try {
    const response = await fetch(feedBase + 'current.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('feed unavailable');
    const manifest = await response.json();
    if (!Array.isArray(manifest.tracks) || !Number.isFinite(manifest.start_epoch_ms) ||
        !Number.isFinite(manifest.updated_epoch_ms) ||
        Date.now() - manifest.updated_epoch_ms > 30000) {
      throw new Error('feed stale');
    }
    const track = selectedTrack(manifest);
    if (track !== 'off' && !manifest.tracks.includes(track)) {
      throw new Error('track unavailable');
    }
    if (track !== 'off') {
      const vtt = await fetch(feedBase + encodeURIComponent(track) + '.vtt', { cache: 'no-store' });
      if (!vtt.ok) throw new Error('track unavailable');
      cues = parseVtt(await vtt.text());
    } else {
      cues = [];
    }
    current = manifest;
    const nextStatus = track === 'off' ? 'Captions off.' : 'Live captions available.';
    if (status.textContent !== nextStatus) status.textContent = nextStatus;
    render();
  } catch {
    current = null;
    cues = [];
    overlay.textContent = '';
    const message = 'Live captions are unavailable here right now. You can try the CC control in the video player.';
    if (status.textContent !== message) status.textContent = message;
  }
  window.setTimeout(refresh, 3000);
}

async function loadArchive() {
  try {
    const response = await fetch(archiveBase + 'index.json');
    if (!response.ok) return;
    const rotations = await response.json();
    if (!Array.isArray(rotations) || rotations.length === 0) return;
    archiveList.replaceChildren();
    for (const item of rotations.slice(-20).reverse()) {
      if (!/^[a-zA-Z0-9-]+$/.test(item.rotation) || !Array.isArray(item.tracks)) continue;
      const entry = document.createElement('li');
      entry.append(document.createTextNode(item.rotation + ': '));
      for (const track of item.tracks) {
        if (!/^[a-z0-9-]+$/.test(track)) continue;
        const link = document.createElement('a');
        link.href = archiveBase + item.rotation + '/' + track + '.vtt';
        link.textContent = track;
        entry.append(link, document.createTextNode(' '));
      }
      archiveList.append(entry);
    }
  } catch {
    // The archive is optional until the first rotation has been published.
  }
}

trackSelect.addEventListener('change', render);
delayInput.addEventListener('input', render);
window.setInterval(render, 250);
refresh();
loadArchive();
