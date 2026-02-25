/**
 * MemeForge — Editor JS
 * Handles: image upload, drag & drop, template selection,
 *          real-time canvas rendering, download, share, save.
 */

// ── Canvas setup ──────────────────────────────────────────────
const canvas      = document.getElementById('meme-canvas');
const ctx         = canvas.getContext('2d');
const placeholder = document.getElementById('canvas-placeholder');
const canvasInfo  = document.getElementById('canvas-info');

let currentImage = null;
let history      = [];    
let isBold       = true;
let isItalic     = false;
let isUpperCase  = true;
let selectedFont = 'Impact';

// ── Meme Templates (placeholder colors, replace with real img paths) ──
const TEMPLATES = [
  { name: 'Drake',       url: 'https://i.imgflip.com/30b1gx.jpg' },
  { name: 'Distracted',  url: 'https://i.imgflip.com/1ur9b0.jpg' },
  { name: 'Two Buttons', url: 'https://i.imgflip.com/1g8my4.jpg' },
  { name: 'Change My Mind', url: 'https://i.imgflip.com/24y43o.jpg' },
];

// ── Build template grid ───────────────────────────────────────
const templateGrid = document.getElementById('template-grid');
TEMPLATES.forEach((t, i) => {
  const div = document.createElement('div');
  div.className = 'template-thumb';
  div.title = t.name;
  div.innerHTML = `<img src="${t.url}" alt="${t.name}" loading="lazy">`;
  div.addEventListener('click', () => {
    document.querySelectorAll('.template-thumb').forEach(el => el.classList.remove('selected'));
    div.classList.add('selected');
    loadImageFromURL(t.url);
  });
  templateGrid.appendChild(div);
});

// ── Load image from URL ───────────────────────────────────────
function loadImageFromURL(url) {
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => {
    currentImage = img;
    resizeCanvas(img);
    drawMeme();
    showCanvas();
    pushHistory();
  };
  img.onerror = () => showToast('❌ Impossible de charger cette image');
  img.src = url;
}

function resizeCanvas(img) {
  const MAX_W = canvas.parentElement.clientWidth - 4;
  const ratio = img.naturalHeight / img.naturalWidth;
  canvas.width  = Math.min(MAX_W, img.naturalWidth);
  canvas.height = canvas.width * ratio;
}

function showCanvas() {
  canvas.style.display = 'block';
  placeholder.style.display = 'none';
  canvasInfo.textContent = `${canvas.width}×${canvas.height}px`;
  enableButtons();
}

// ── Draw function (called on every input change) ──────────────
function drawMeme() {
  if (!currentImage) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(currentImage, 0, 0, canvas.width, canvas.height);

  const topText    = document.getElementById('top-text').value;
  const bottomText = document.getElementById('bottom-text').value;

  if (topText || bottomText) {
    if (topText)    drawText(topText,    'top');
    if (bottomText) drawText(bottomText, 'bottom');
  }
}

function drawText(text, position) {
  const sizeId    = position === 'top' ? 'top-size'    : 'bottom-size';
  const colorId   = position === 'top' ? 'top-color'   : 'bottom-color';
  const strokeId  = position === 'top' ? 'top-stroke'  : 'bottom-stroke';
  const strokeW   = parseInt(document.getElementById('stroke-width').value);

  let fontSize    = parseInt(document.getElementById(sizeId).value);
  const fillColor = document.getElementById(colorId).value;
  const strColor  = document.getElementById(strokeId).value;

  // Scale font to canvas width
  const scaleFactor = canvas.width / 600;
  fontSize = Math.round(fontSize * scaleFactor);

  const fontStyle = `${isItalic ? 'italic ' : ''}${isBold ? 'bold ' : ''}${fontSize}px ${selectedFont}`;
  ctx.font      = fontStyle;
  ctx.textAlign = 'center';
  ctx.lineJoin  = 'round';

  const displayText = isUpperCase ? text.toUpperCase() : text;
  const maxWidth    = canvas.width * 0.92;
  const lines       = wrapText(displayText, maxWidth);
  const lineHeight  = fontSize * 1.2;

  const totalHeight = lines.length * lineHeight;
  const padding     = fontSize * 0.4;

  let y;
  if (position === 'top') {
    y = padding + fontSize;
  } else {
    y = canvas.height - padding - totalHeight + fontSize;
  }

  lines.forEach(line => {
    if (strokeW > 0) {
      ctx.strokeStyle = strColor;
      ctx.lineWidth   = strokeW * scaleFactor * 2;
      ctx.strokeText(line, canvas.width / 2, y);
    }
    ctx.fillStyle = fillColor;
    ctx.fillText(line, canvas.width / 2, y);
    y += lineHeight;
  });
}

function wrapText(text, maxWidth) {
  const words = text.split(' ');
  const lines = [];
  let current = '';

  for (const word of words) {
    const test = current ? current + ' ' + word : word;
    if (ctx.measureText(test).width <= maxWidth) {
      current = test;
    } else {
      if (current) lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return lines.length ? lines : [''];
}

// ── History (undo) ────────────────────────────────────────────
function pushHistory() {
  history.push(canvas.toDataURL());
  if (history.length > 20) history.shift();
}

document.getElementById('btn-undo').addEventListener('click', () => {
  if (history.length > 1) {
    history.pop();
    const prev = new Image();
    prev.onload = () => {
      currentImage = prev;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(prev, 0, 0, canvas.width, canvas.height);
    };
    prev.src = history[history.length - 1];
  }
});

document.getElementById('btn-reset').addEventListener('click', () => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  currentImage = null;
  canvas.style.display  = 'none';
  placeholder.style.display = '';
  canvasInfo.textContent = 'Aucune image chargée';
  history = [];
  disableButtons();
  document.querySelectorAll('.template-thumb').forEach(el => el.classList.remove('selected'));
});

// ── Image upload ──────────────────────────────────────────────
document.getElementById('image-input').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) loadFile(file);
});

function loadFile(file) {
  if (!file.type.startsWith('image/')) {
    showToast('❌ Format non supporté'); return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast('❌ Fichier trop lourd (max 10 Mo)'); return;
  }
  const url = URL.createObjectURL(file);
  loadImageFromURL(url);
}

// ── Drag & drop ───────────────────────────────────────────────
const dropZone = document.getElementById('canvas-drop-zone');
const uploadLabel = document.getElementById('upload-label');

[dropZone, uploadLabel].forEach(el => {
  el.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  el.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  el.addEventListener('drop', e => {
    e.preventDefault(); dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) loadFile(file);
  });
});

// ── Live redraw on input ──────────────────────────────────────
const liveInputs = ['top-text','bottom-text','top-size','bottom-size',
                    'top-color','bottom-color','top-stroke','bottom-stroke','stroke-width'];
liveInputs.forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener('input', drawMeme);
  if (el.type === 'range') {
    el.addEventListener('input', () => {
      const valEl = document.getElementById(id + '-val');
      if (valEl) valEl.textContent = el.value;
    });
  }
});

// ── Font selection ────────────────────────────────────────────
document.getElementById('font-pills').addEventListener('click', e => {
  const pill = e.target.closest('.font-pill');
  if (!pill) return;
  document.querySelectorAll('.font-pill').forEach(p => p.classList.remove('active'));
  pill.classList.add('active');
  selectedFont = pill.dataset.font;
  drawMeme();
});

// ── Style toggles ─────────────────────────────────────────────
document.getElementById('toggle-bold').addEventListener('click', function () {
  isBold = !isBold; this.classList.toggle('active', isBold); drawMeme();
});
document.getElementById('toggle-italic').addEventListener('click', function () {
  isItalic = !isItalic; this.classList.toggle('active', isItalic); drawMeme();
});
document.getElementById('toggle-caps').addEventListener('click', function () {
  isUpperCase = !isUpperCase; this.classList.toggle('active', isUpperCase); drawMeme();
});

// ── Download ──────────────────────────────────────────────────
document.getElementById('btn-download').addEventListener('click', () => {
  if (!currentImage) return;
  drawMeme(); // fresh render
  const link = document.createElement('a');
  link.download = 'meme-memeforge.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
  showToast('✅ Mème téléchargé !');
  pushHistory();
});

// ── Share ─────────────────────────────────────────────────────
// NOTE : le partage depuis l'éditeur n'est disponible qu'APRÈS sauvegarde.
// On désactive les boutons partage ici et on les réactive dans enableButtons()
// seulement après que l'utilisateur ait explicitement sauvegardé le mème.
// La variable lastSavedDetailUrl est mise à jour par le serveur via redirect.
// Pour l'instant on redirige vers la galerie après save, donc les boutons
// de partage depuis l'éditeur pointent vers la galerie principale.
function getShareURL() {
  return `${window.location.origin}/gallery/`;
}

document.getElementById('btn-share-fb').addEventListener('click', () => {
  window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(getShareURL())}`, '_blank');
});
document.getElementById('btn-share-tw').addEventListener('click', () => {
  window.open(`https://twitter.com/intent/tweet?text=Mon+mème+créé+sur+MemeForge+⚡&url=${encodeURIComponent(getShareURL())}`, '_blank');
});
document.getElementById('btn-share-wa').addEventListener('click', () => {
  window.open(`https://wa.me/?text=Regarde+mon+mème+!+${encodeURIComponent(getShareURL())}`, '_blank');
});

// ── Save to gallery ───────────────────────────────────────────
document.getElementById('save-form').addEventListener('submit', (e) => {
  if (!currentImage) { e.preventDefault(); showToast('❌ Aucune image à sauvegarder'); return; }
  drawMeme();

  // Champs image + textes
  document.getElementById('meme-data-input').value = canvas.toDataURL('image/png');
  document.getElementById('hidden-top').value       = document.getElementById('top-text').value;
  document.getElementById('hidden-bottom').value    = document.getElementById('bottom-text').value;

  // Typographie — synchronisés avec l'état JS courant
  document.getElementById('hidden-font-name').value    = selectedFont;
  document.getElementById('hidden-font-size-top').value = document.getElementById('top-size').value;
  document.getElementById('hidden-font-size-bot').value = document.getElementById('bottom-size').value;
  document.getElementById('hidden-color-top').value    = document.getElementById('top-color').value;
  document.getElementById('hidden-color-bottom').value = document.getElementById('bottom-color').value;
  // Contour : couleurs séparées haut et bas (correspondent aux champs backend)
  document.getElementById('hidden-stroke-color-top').value = document.getElementById('top-stroke').value;
  document.getElementById('hidden-stroke-color-bot').value = document.getElementById('bottom-stroke').value;
  document.getElementById('hidden-stroke-width').value = document.getElementById('stroke-width').value;
  // Booléens : le backend attend 'on' / '' (comportement Django BooleanField)
  document.getElementById('hidden-is-bold').value     = isBold     ? 'on' : '';
  document.getElementById('hidden-is-italic').value   = isItalic   ? 'on' : '';
  document.getElementById('hidden-is-uppercase').value = isUpperCase ? 'on' : '';

  showToast('💾 Sauvegarde en cours...');
});

// ── Enable / Disable buttons ──────────────────────────────────
function enableButtons() {
  document.getElementById('btn-download').disabled  = false;
  document.getElementById('btn-save').disabled      = false;
  document.getElementById('btn-share-fb').disabled  = false;
  document.getElementById('btn-share-tw').disabled  = false;
  document.getElementById('btn-share-wa').disabled  = false;
}
function disableButtons() {
  ['btn-download','btn-save','btn-share-fb','btn-share-tw','btn-share-wa']
    .forEach(id => document.getElementById(id).disabled = true);
}

// ── Toast ─────────────────────────────────────────────────────
function showToast(msg, duration = 2800) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

// ── Init ──────────────────────────────────────────────────────
disableButtons();