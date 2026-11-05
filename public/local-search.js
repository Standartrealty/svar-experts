(async()=>{
const form=document.getElementById('catalog-search'),input=form.elements.q,results=document.getElementById('results');
const data=await fetch('/catalog-data.json').then(r=>r.json());
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function show(){const q=input.value.trim().toLowerCase();const products=q?data.products.filter(p=>(p.title+' '+p.brand+' '+p.text.replace(/<[^>]*>/g,' ')).toLowerCase().includes(q)):[];results.innerHTML='<p>'+ (q?'Найдено товаров: '+products.length:'Введите название товара или бренд')+'</p><div class="grid">'+products.map(p=>{const image=JSON.parse(p.gallery||'[]')[0]?.img;return '<a class="card" href="'+esc(p.url)+'">'+(image?'<img src="'+esc(image)+'" alt="'+esc(p.title)+'">':'')+'<h2>'+esc(p.title)+'</h2><p>'+esc(p.brand||'')+'</p>'+(p.price?'<strong>'+Number(p.price).toLocaleString('ru-RU')+' ₽</strong>':'')+'</a>';}).join('')+'</div>';}
form.addEventListener('submit',e=>{e.preventDefault();history.replaceState(null,'','/search?q='+encodeURIComponent(input.value));show();});input.value=new URLSearchParams(location.search).get('q')||new URLSearchParams(location.search).get('search')||'';show();
})();
