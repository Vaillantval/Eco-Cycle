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
}

const hamburger = document.getElementById('hamburger');
if (hamburger) {
  hamburger.addEventListener('click', toggleMenu);
}

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
