// ── PHOTO PREVIEW ──
const photoInput = document.getElementById('photo-input');
const photoPreview = document.getElementById('photo-preview');
const uploadArea = document.getElementById('upload-area');

if (photoInput) {
  photoInput.addEventListener('change', () => {
    const file = photoInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      photoPreview.src = e.target.result;
      photoPreview.style.display = 'block';
      uploadArea.classList.add('has-file');
    };
    reader.readAsDataURL(file);
  });

  uploadArea.addEventListener('click', () => photoInput.click());
  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--green)';
  });
  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      photoInput.files = dt.files;
      photoInput.dispatchEvent(new Event('change'));
    }
  });
}

// ── AI ANALYSIS ──
const btnAnalyze = document.getElementById('btn-analyze');
if (btnAnalyze) {
  btnAnalyze.addEventListener('click', async () => {
    const file = photoInput && photoInput.files[0];
    if (!file) {
      alert("Sélectionnez d'abord une photo.");
      return;
    }

    const loading   = document.getElementById('ai-loading');
    const resultBox = document.getElementById('ai-result');

    loading.style.display = 'block';
    resultBox.classList.remove('visible');
    btnAnalyze.disabled = true;
    btnAnalyze.textContent = 'Analyse en cours...';

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const response = await fetch('/api/waste/analyze/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
          },
          body: JSON.stringify({ image_base64: e.target.result }),
        });

        const data = await response.json();
        loading.style.display = 'none';
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🤖 Analyser avec l\'IA';

        if (data.analysis) {
          const a = data.analysis;
          resultBox.classList.add('visible');
          document.getElementById('ai-category').textContent  = a.category    || '—';
          document.getElementById('ai-value').textContent     = (a.estimated_value_htg || '—') + ' HTG';
          document.getElementById('ai-score').textContent     = (a.recyclability_score || '—') + '/10';
          document.getElementById('ai-condition').textContent = a.condition   || '—';
          document.getElementById('ai-description').textContent = a.description || '—';

          // Pré-remplir les champs du formulaire si vides
          const titleInput  = document.getElementById('title-input');
          const weightInput = document.getElementById('weight-input');
          if (titleInput  && !titleInput.value)  titleInput.value  = a.category || '';
          if (weightInput && !weightInput.value) weightInput.value = a.estimated_weight_kg || '';
        } else {
          alert("Analyse impossible. Vérifiez que la photo est claire et réessayez.");
        }
      } catch (err) {
        loading.style.display = 'none';
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🤖 Analyser avec l\'IA';
        alert("Erreur lors de l'analyse. Réessayez.");
      }
    };
    reader.readAsDataURL(file);
  });
}
