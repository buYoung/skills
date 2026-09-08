import '@fixture/theme';
const counter = document.getElementById('counter');
counter.addEventListener('click', () => { counter.textContent = String(Number(counter.textContent) + 1); });
