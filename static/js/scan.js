async function submitScan(e){
  e.preventDefault();
  const btn = document.getElementById('btnGo');
  btn.disabled = true;
  const body = {
    typ:'BOOK',
    qr: document.getElementById('qr').value,
    id: document.getElementById('book_id').value || null,
    ts: Math.floor(Date.now()/1000),
    student_fid: document.getElementById('fid').value,
    processed_by: 'self'  // backend will replace with session user
  };
  const r = await fetch('/api/library/scan', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const j = await r.json();
  document.getElementById('scanResult').textContent = JSON.stringify(j,null,2);
  btn.disabled = false;
  return false;
}
