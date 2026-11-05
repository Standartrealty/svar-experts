const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const data=JSON.parse(fs.readFileSync('public/catalog-data.json'));
assert.equal(data.products.length,332);assert.equal(new Set(data.products.map(p=>p.uid)).size,332);
let photos=0,descriptions=0;
for(const p of data.products){
 assert.ok(p.title);assert.ok(fs.existsSync('public'+new URL(p.url,'http://local').pathname+'.html'),p.url);
 if(p.text||p.descr)descriptions++;
 for(const g of JSON.parse(p.gallery||'[]')){assert.ok(g.img.startsWith('/assets/'),g.img);assert.ok(fs.existsSync('public'+g.img),g.img);photos++;}
}
for(const p of ['index','catalog','search','yokomotobrend','sales','privacypolicy','forbusiness','forb2bsales','service','agronent'])assert.ok(fs.existsSync('public/'+p+'.html'));
const {catalog}=require('./api/catalog');
assert.equal(catalog({}).total,332);assert.equal(catalog({slice:'10'}).products.length,8);
const ids=new Set();for(let slice=1;slice<=10;slice++)for(const p of catalog({slice}).products)ids.add(p.uid);assert.equal(ids.size,332);
for(const part of data.parts)assert.ok(catalog({storepartuid:String(part.uid)}).total>0);
assert.ok(catalog({'filters[brand]':'YOKOMOTO'}).products.every(p=>p.brand==='YOKOMOTO'));
for(const alias of ['544983720072-motopompa-yokomoto-50cx','880477745052-generator-yokomoto-4000-ix'])assert.ok(fs.existsSync('public/catalog/tproduct/'+alias+'.html'));
console.log(JSON.stringify({products:332,photos,descriptions,categories:data.parts.length,checks:'passed'},null,2));
