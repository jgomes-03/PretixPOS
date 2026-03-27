(function () {
  const ctx = window.BETTERPOS_CONTEXT;
  if (!ctx) return;

  async function fetchCatalog() {
    const url = new URL('api/catalog/', window.location.href).toString();
    const res = await fetch(url, { credentials: 'same-origin' });
    if (!res.ok) return;
    const data = await res.json();
    const target = document.getElementById('catalog-root');
    target.innerHTML = data.items.map(i => `<div>${i.name} - ${i.price}</div>`).join('');
  }

  fetchCatalog();
})();
