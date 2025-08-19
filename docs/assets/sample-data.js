// Örnek veri üretimi (statik mod için)
(function(){
  function pad(n){ return n < 10 ? '0'+n : ''+n; }
  function ts(d){
    const y=d.getFullYear(), m=pad(d.getMonth()+1), da=pad(d.getDate());
    const h=pad(d.getHours()), mi=pad(d.getMinutes()), s=pad(d.getSeconds());
    return `${y}-${m}-${da} ${h}:${mi}:${s}`;
  }
  function rand(min, max){ return Math.random()*(max-min)+min; }

  const locations = ['Ofis A','Ofis B','Depo','Laboratuvar'];
  const sensors = ['SENSOR001','SENSOR002','SENSOR003','SENSOR004'];
  const now = new Date();

  const rows = [];
  let id = 1;
  for(let i=0;i<50;i++){
    const d = new Date(now.getTime() - i*60*60*1000);
    const base = 26 + (i%4);
    const sicaklik = Number((base + rand(-1.0, 2.5)).toFixed(1));
    const nem = Number(rand(45, 70).toFixed(1));
    const idx = i % 4;
    rows.push({
      id: id++,
      sensor_id: sensors[idx],
      sicaklik,
      nem,
      lokasyon: locations[idx],
      timestamp: ts(d)
    });
  }

  window.STATIC_SAMPLE = {
    total: rows.length,
    data: rows.reverse()
  };
})();


