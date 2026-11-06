document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.card');
  const panels = document.querySelectorAll('.panel');
  const grid = document.querySelector('.emergency-grid');
  const disclaimer = document.querySelector('.disclaimer');

  // Open panel
  cards.forEach(card => {
    card.addEventListener('click', () => {
      const targetId = card.dataset.target;
      const panel = document.getElementById(targetId);
      
      if (panel) {
        // Hide grid and disclaimer
        grid.style.display = 'none';
        if (disclaimer) disclaimer.style.display = 'none';
        
        // Hide all panels then show target
        panels.forEach(p => p.classList.add('hidden'));
        panel.classList.remove('hidden');
        
        // Scroll to top of content
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  });

  // Back buttons
  document.querySelectorAll('.back-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      panels.forEach(p => p.classList.add('hidden'));
      grid.style.display = 'grid';
      if (disclaimer) disclaimer.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
});
