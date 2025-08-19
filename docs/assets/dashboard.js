// Statik dashboard davranışı (backend yok)
(function(){
  const sample = window.STATIC_SAMPLE || { total: 0, data: [] };

  const tableBody = document.getElementById('tableBody');
  const statTotal = document.getElementById('statTotal');
  const statAvg = document.getElementById('statAvg');
  const statMax = document.getElementById('statMax');
  const statMin = document.getElementById('statMin');
  const locationFilter = document.getElementById('locationFilter');
  const searchInput = document.getElementById('searchInput');
  const pagination = document.getElementById('pagination');
  const sortAscBtn = document.getElementById('sortAsc');
  const sortDescBtn = document.getElementById('sortDesc');
  const btnRefresh = document.getElementById('btnRefresh');
  const btnExport = document.getElementById('btnExport');

  let currentPage = 1;
  const perPage = 20;
  let currentData = sample.data.slice();

  function updateStats(items){
    const temps = items.map(r=>r.sicaklik);
    const avg = temps.length ? (temps.reduce((a,b)=>a+b,0)/temps.length) : 0;
    const max = temps.length ? Math.max(...temps) : 0;
    const min = temps.length ? Math.min(...temps) : 0;
    statTotal.textContent = sample.total;
    statAvg.textContent = `${avg.toFixed(1)}°C`;
    statMax.textContent = `${max.toFixed(1)}°C`;
    statMin.textContent = `${min.toFixed(1)}°C`;
  }

  function renderTable(items){
    tableBody.innerHTML = '';
    items.forEach(veri => {
      const tr = document.createElement('tr');
      const tempClass = veri.sicaklik > 30 ? 'temperature-high' : (veri.sicaklik < 15 ? 'temperature-low' : 'temperature-normal');
      tr.innerHTML = `
        <td>${veri.id}</td>
        <td>${veri.sensor_id}</td>
        <td data-value="${veri.sicaklik}"><span class="${tempClass}">${veri.sicaklik.toFixed(1)}°C</span></td>
        <td>${veri.nem.toFixed(1)}%</td>
        <td>${veri.lokasyon}</td>
        <td>${veri.timestamp}</td>
      `;
      tableBody.appendChild(tr);
    });
  }

  function renderPagination(total){
    const pages = Math.max(1, Math.ceil(total / perPage));
    pagination.innerHTML = '';
    const prev = document.createElement('li');
    prev.className = `page-item ${currentPage===1?'disabled':''}`;
    prev.innerHTML = `<a class="page-link" href="#">Önceki</a>`;
    prev.onclick = (e)=>{ e.preventDefault(); if(currentPage>1){ currentPage--; update(); } };
    pagination.appendChild(prev);
    for(let i=1;i<=pages;i++){
      const li = document.createElement('li');
      li.className = `page-item ${i===currentPage?'active':''}`;
      li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
      li.onclick = (e)=>{ e.preventDefault(); currentPage=i; update(); };
      pagination.appendChild(li);
    }
    const next = document.createElement('li');
    next.className = `page-item ${currentPage===pages?'disabled':''}`;
    next.innerHTML = `<a class="page-link" href="#">Sonraki</a>`;
    next.onclick = (e)=>{ e.preventDefault(); if(currentPage<pages){ currentPage++; update(); } };
    pagination.appendChild(next);
  }

  function applyFilters(){
    const term = (searchInput.value || '').toLowerCase();
    const loc = (locationFilter.value || '').toLowerCase();
    return sample.data.filter(r => {
      const matchesTerm = !term || `${r.id} ${r.sensor_id} ${r.sicaklik} ${r.nem} ${r.lokasyon} ${r.timestamp}`.toLowerCase().includes(term);
      const matchesLoc = !loc || r.lokasyon.toLowerCase().includes(loc);
      return matchesTerm && matchesLoc;
    });
  }

  function updateLocationFilter(){
    const set = new Set(sample.data.map(r=>r.lokasyon));
    locationFilter.innerHTML = '<option value="">Tüm Lokasyonlar</option>' +
      Array.from(set).map(l=>`<option value="${l}">${l}</option>`).join('');
  }

  function updateChart(items){
    const ctx = document.getElementById('temperatureChart').getContext('2d');
    const labels = items.map(r=>r.timestamp.split(' ')[1]);
    const temps = items.map(r=>r.sicaklik);
    const hums = items.map(r=>r.nem);
    if(window._chart){ window._chart.destroy(); }
    window._chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [
        { label: 'Sıcaklık (°C)', data: temps, borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,.1)', tension:.4, fill:true },
        { label: 'Nem (%)', data: hums, borderColor: '#e74c3c', backgroundColor: 'rgba(231,76,60,.1)', tension:.4, fill:true, yAxisID:'y1' }
      ]},
      options: { responsive:true, maintainAspectRatio:false, scales:{ y:{ beginAtZero:false }, y1:{ position:'right', beginAtZero:false, max:100 } } }
    });
  }

  function update(){
    const filtered = applyFilters();
    updateStats(filtered);
    const start = (currentPage-1) * perPage;
    const pageItems = filtered.slice(start, start+perPage);
    renderTable(pageItems);
    renderPagination(filtered.length);
    updateChart(pageItems);
  }

  // Events
  searchInput.addEventListener('input', ()=>{ currentPage=1; update(); });
  locationFilter.addEventListener('change', ()=>{ currentPage=1; update(); });
  sortAscBtn.addEventListener('click', ()=>{ sample.data.sort((a,b)=>a.sicaklik-b.sicaklik); currentPage=1; update(); });
  sortDescBtn.addEventListener('click', ()=>{ sample.data.sort((a,b)=>b.sicaklik-a.sicaklik); currentPage=1; update(); });
  btnRefresh.addEventListener('click', ()=>{ update(); });
  btnExport.addEventListener('click', ()=>{
    const headers = ['ID','Sensor ID','Sıcaklık','Nem','Lokasyon','Tarih/Saat'];
    const rows = applyFilters().map(r=>[r.id,r.sensor_id,r.sicaklik,r.nem,r.lokasyon,r.timestamp].join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'isi_verileri.csv';
    link.click();
  });

  // Init
  updateLocationFilter();
  update();
})();


