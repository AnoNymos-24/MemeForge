const modal    = document.getElementById('share-modal');
const backdrop = document.getElementById('modal-backdrop');
const modalFb  = document.getElementById('modal-fb');
const modalTw  = document.getElementById('modal-tw');
const modalWa  = document.getElementById('modal-wa');
const modalUrl = document.getElementById('modal-url');

function openShareModal(relativeUrl) {

  const absoluteUrl = relativeUrl.startsWith('http')
    ? relativeUrl
    : `${window.location.origin}${relativeUrl}`;
  modalUrl.value = absoluteUrl;
  const enc = encodeURIComponent(absoluteUrl);
  modalFb.href = `https://www.facebook.com/sharer/sharer.php?u=${enc}`;
  modalTw.href = `https://twitter.com/intent/tweet?url=${enc}&text=Regarde+mon+mème+%E2%9A%A1`;
  modalWa.href = `https://wa.me/?text=Regarde+mon+mème+!+${enc}`;
  modal.classList.add('open');
  backdrop.classList.add('open');
}

function closeModal() {
  modal.classList.remove('open');
  backdrop.classList.remove('open');
}

document.getElementById('modal-close').addEventListener('click', closeModal);
backdrop.addEventListener('click', closeModal);

// Share buttons in gallery cards
document.querySelectorAll('.share-overlay-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    openShareModal(btn.dataset.url);
  });
});


document.getElementById('modal-copy').addEventListener('click', () => {
  navigator.clipboard.writeText(modalUrl.value)
    .then(() => showToast('🔗 Lien copié !'))
    .catch(() => {
      modalUrl.select();
      document.execCommand('copy');
      showToast('🔗 Lien copié !');
    });
});

function showToast(msg, duration = 2800) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}