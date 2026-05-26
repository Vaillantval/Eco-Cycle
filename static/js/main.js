// ── NAV SCROLL ──
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  });
}

// ── MOBILE MENU ──
function toggleMenu() {
  const menu = document.getElementById('mobileMenu');
  if (menu) menu.classList.toggle('open');
  document.body.style.overflow = menu && menu.classList.contains('open') ? 'hidden' : '';
}

const hamburger = document.getElementById('hamburger');
if (hamburger) hamburger.addEventListener('click', toggleMenu);

const mobileClose = document.getElementById('mobileClose');
if (mobileClose) mobileClose.addEventListener('click', toggleMenu);

// ferme le menu si on clique sur un lien
document.querySelectorAll('.mobile-menu a').forEach(a => {
  a.addEventListener('click', () => {
    const menu = document.getElementById('mobileMenu');
    if (menu) { menu.classList.remove('open'); document.body.style.overflow = ''; }
  });
});

// ── REVEAL ON SCROLL ──
const reveals = document.querySelectorAll('.reveal');
if (reveals.length) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => entry.target.classList.add('visible'), i * 60);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  reveals.forEach(el => observer.observe(el));
}

// ── HOW IT WORKS ──
const steps = document.querySelectorAll('.how-step');
const howData = [
  { icon: '📷', title: 'Scanner IA', sub: 'Pointez votre téléphone sur n\'importe quel déchet' },
  { icon: '🤖', title: 'Analyse instantanée', sub: 'Obtenez le type de matériau et sa valeur marchande en 3 secondes' },
  { icon: '🚚', title: 'Planifier ou enchérir', sub: 'Réservez un ramassage ou publiez sur le marketplace' },
  { icon: '💰', title: 'Encaissez & mesurez l\'impact', sub: 'Recevez votre paiement et suivez votre CO₂ économisé' },
];
if (steps.length) {
  steps.forEach(step => {
    step.addEventListener('click', () => {
      steps.forEach(s => s.classList.remove('active'));
      step.classList.add('active');
      const idx = parseInt(step.dataset.step);
      const icon = document.getElementById('howIcon');
      const title = document.getElementById('howTitle');
      const sub = document.getElementById('howSub');
      if (icon) icon.textContent = howData[idx].icon;
      if (title) title.textContent = howData[idx].title;
      if (sub) sub.textContent = howData[idx].sub;
    });
  });
}

// ── FAQ ──
function toggleFaq(el) {
  const item = el.parentElement;
  const wasOpen = item.classList.contains('open');
  document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
  if (!wasOpen) item.classList.add('open');
}

// ── COUNTER ANIMATION ──
const statsSection = document.getElementById('stats');
if (statsSection) {
  const targets = [10, 5, 120, 800];
  const ids = ['stat1', 'stat2', 'stat3', 'stat4'];
  let counted = false;
  const statsObs = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !counted) {
      counted = true;
      ids.forEach((id, i) => {
        const el = document.getElementById(id);
        if (!el) return;
        let count = 0;
        const end = targets[i];
        const step = Math.max(1, Math.floor(end / 40));
        const timer = setInterval(() => {
          count = Math.min(count + step, end);
          el.textContent = count;
          if (count >= end) clearInterval(timer);
        }, 40);
      });
    }
  }, { threshold: 0.4 });
  statsObs.observe(statsSection);
}

// ── AUCTION COUNTDOWN ──
function updateCountdowns() {
  document.querySelectorAll('[data-ends-at]').forEach(el => {
    const endsAt = new Date(el.dataset.endsAt);
    const now = new Date();
    const diff = endsAt - now;
    if (diff <= 0) {
      el.textContent = 'Terminée';
      el.classList.add('expired');
      return;
    }
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    el.textContent = `${h}h ${m}m ${s}s`;
  });
}
if (document.querySelector('[data-ends-at]')) {
  updateCountdowns();
  setInterval(updateCountdowns, 1000);
}

// ── AUTO-DISMISS FLASH MESSAGES ──
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(alert => {
    alert.style.opacity = '0';
    alert.style.transition = 'opacity 0.4s';
    setTimeout(() => alert.remove(), 400);
  });
}, 5000);

// ── FORM SUBMIT FEEDBACK ──
const formSubmit = document.querySelector('.form-submit');
if (formSubmit) {
  formSubmit.addEventListener('click', function() {
    this.textContent = '✅ Message envoyé !';
    this.style.background = 'var(--green-light)';
    setTimeout(() => {
      this.textContent = 'Envoyer →';
      this.style.background = '';
    }, 3000);
  });
}

const newsletterBtn = document.querySelector('.newsletter-btn');
if (newsletterBtn) {
  newsletterBtn.addEventListener('click', function() {
    this.textContent = '✅ Inscrit !';
    setTimeout(() => { this.textContent = 'S\'abonner'; }, 3000);
  });
}

// ── IMAGE SLIDER ──
(function () {
  const track    = document.getElementById('sliderTrack');
  const dots     = document.querySelectorAll('.slider-dot');
  const progress = document.getElementById('sliderProgress');
  const btnPrev  = document.getElementById('sliderPrev');
  const btnNext  = document.getElementById('sliderNext');
  if (!track) return;

  const TOTAL = dots.length || 1;
  const DELAY = 5000;
  let current = 0;
  let timer   = null;

  function goTo(idx) {
    current = (idx + TOTAL) % TOTAL;
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
    resetProgress();
  }

  function resetProgress() {
    if (!progress) return;
    progress.style.transition = 'none';
    progress.style.width = '0%';
    requestAnimationFrame(() => requestAnimationFrame(() => {
      progress.style.transition = `width ${DELAY}ms linear`;
      progress.style.width = '100%';
    }));
  }

  function startAuto() {
    clearInterval(timer);
    timer = setInterval(() => goTo(current + 1), DELAY);
  }

  dots.forEach(dot => dot.addEventListener('click', () => {
    goTo(parseInt(dot.dataset.slide)); startAuto();
  }));
  if (btnPrev) btnPrev.addEventListener('click', () => { goTo(current - 1); startAuto(); });
  if (btnNext) btnNext.addEventListener('click', () => { goTo(current + 1); startAuto(); });

  const section = track.closest('#features-slider');
  if (section) {
    section.addEventListener('mouseenter', () => clearInterval(timer));
    section.addEventListener('mouseleave', startAuto);
  }

  if (TOTAL > 1) { resetProgress(); startAuto(); }
})();

// ── CHAT WIDGET CONSEILLER RECYCLAGE ──────────────────────────────────────────
(function () {
  let chatHistory = [];

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  }

  window.toggleChat = function () {
    const box = document.getElementById('chat-box');
    if (!box) return;
    const opening = box.style.display === 'none';
    box.style.display = opening ? 'flex' : 'none';
    if (opening) document.getElementById('chat-input')?.focus();
  };

  window.sendChatMessage = async function () {
    const input = document.getElementById('chat-input');
    const message = input?.value.trim();
    if (!message) return;

    appendChatBubble('user', message);
    input.value = '';
    const loadingId = appendChatBubble('assistant', '...');

    try {
      const res = await fetch('/api/waste/advisor/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ message, history: chatHistory }),
      });
      const data = await res.json();
      removeChatBubble(loadingId);
      if (data.reply) {
        appendChatBubble('assistant', data.reply);
        chatHistory = data.history || [];
      } else {
        appendChatBubble('assistant', data.error || 'Une erreur est survenue.');
      }
    } catch {
      removeChatBubble(loadingId);
      appendChatBubble('assistant', 'Désolé, une erreur est survenue. Réessayez.');
    }
  };

  function appendChatBubble(role, text) {
    const box = document.getElementById('chat-messages');
    if (!box) return null;
    const id  = 'cb-' + Date.now();
    const div = document.createElement('div');
    div.className = `chat-bubble ${role}`;
    div.id        = id;
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return id;
  }

  function removeChatBubble(id) {
    if (id) document.getElementById(id)?.remove();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('chat-toggle')?.addEventListener('click', toggleChat);
    document.getElementById('chat-input')?.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') sendChatMessage();
    });
  });
})();
