const fs = require('node:fs');
const path = require('node:path');
let snapshot;
function catalog(query, body) {
 const normalized={};
 for(const [key,value] of Object.entries(query||{})){
  const name=key.replace(/\[\d+\]$/, '');
  normalized[name]=normalized[name]===undefined?value:[].concat(normalized[name],value);
 }
 query=normalized;
 snapshot ||= JSON.parse(fs.readFileSync(path.join(__dirname, '../public/catalog-data.json'), 'utf8'));
 const operation = query.operation || 'getproductslist';
 let products = snapshot.products.slice();
 const get = name => query[name] ?? query['filters['+name+']'];
 if(operation==='getproductsbyuid') {
  if(typeof body==='string') { try {body=JSON.parse(body);}catch {body={};} }
  const ids = String(body?.productsuid || query.productsuid || '').split(',');
  return {products:products.filter(p=>ids.includes(String(p.uid)))};
 }
 if(operation==='getproduct')return {partuid:snapshot.partuid,product:products.find(p=>String(p.uid)===String(query.productuid))||''};
 if(operation==='getfilters')return snapshot.filters;
 const part = query.storepartuid;
 if(part && String(part)!==String(snapshot.partuid))products=products.filter(p=>JSON.parse(p.partuids||'[]').map(String).includes(String(part)));
 const matches=(value,chosen)=>[].concat(chosen).some(v=>[].concat(value||[]).map(String).includes(String(v)));
 for(const field of ['brand','equipment_type','voltage','nominal_power']){
  const chosen=get(field);
  if(chosen){
   if(field==='brand'){
    const canonical=value=>String(value||'').toUpperCase().replace(/^BONATEC$/, 'BONATEK');
    const accepted=[].concat(chosen).map(canonical);
    products=products.filter(p=>accepted.includes(canonical(p.brand)));
   }else products=products.filter(p=>matches(p[field],chosen));
  }
 }
 const selectedParts=query['filters[storepartuid]'];
 if(selectedParts){
  const ids=[].concat(selectedParts).map(value=>snapshot.parts.find(p=>p.title===value||String(p.uid)===String(value))?.uid).filter(Boolean).map(String);
  if(ids.length)products=products.filter(p=>JSON.parse(p.partuids||'[]').some(id=>ids.includes(String(id))));
 }
 const search=get('search')||get('query')||'';
 if(search)products=products.filter(p=>(p.title+' '+p.brand+' '+p.text.replace(/<[^>]*>/g,' ')).toLowerCase().includes(String(search).toLowerCase()));
 const sort=query.sort||'';
 if(sort.includes('price')) products.sort((a,b)=>(Number(a.price)-Number(b.price))*(sort.includes('desc')?-1:1));
 if(sort.includes('title'))products.sort((a,b)=>a.title.localeCompare(b.title,'ru')*(sort.includes('desc')?-1:1));
 const total=products.length;
 const slice=Math.max(1,Number(query.slice)||1), size=36;
 if(operation==='getrelevantproducts')return {relevants:products.filter(p=>String(p.uid)!==String(query.productuid)).slice(0,Number(query.quantity)||4)};
 return {...snapshot,products:products.slice((slice-1)*size,slice*size),total,slice,nextslice:slice*size<total?slice+1:null};
}
module.exports=(req,res)=>{res.setHeader('Cache-Control','public, max-age=300');res.status(200).json(catalog(req.query,req.body));};
module.exports.catalog=catalog;
