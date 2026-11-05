const assert=require('node:assert/strict'),fs=require('node:fs');
const data=JSON.parse(fs.readFileSync('public/catalog-data.json'));
const report=JSON.parse(fs.readFileSync('source/catalog-import-2026-11-06.json'));
assert.equal(data.products.length,332+report.addedProducts);assert.equal(data.products.length,report.totalProducts);
assert.equal(new Set(data.products.map(p=>p.uid)).size,data.products.length);
let photos=0,descriptions=0;
const byId=new Map(data.products.map(p=>[p.uid,p]));
for(const p of data.products){
 assert.ok(p.title);assert.ok(fs.existsSync('public'+new URL(p.url,'http://local').pathname+'.html'),p.url);
 if(p.text||p.descr)descriptions++;
 for(const g of JSON.parse(p.gallery||'[]')){assert.ok(g.img.startsWith('/assets/'),g.img);assert.ok(fs.existsSync('public'+g.img),g.img);photos++;}
}
for(const name of ['index','catalog','search','yokomotobrend','sales','privacypolicy','forbusiness','forb2bsales','service','agronent'])assert.ok(fs.existsSync('public/'+name+'.html'));
const excluded=new Set(report.excluded.map(r=>r.brand+':'+r.row));
assert.equal(excluded.size,28);
const sourceRows=new Set();
for(const r of report.records){
 const sourceBrand=r.source.file.includes('Bonatek')?'BONATEK':r.source.file.includes('VOLBERRY')?'VOLTBERRY':'YOKOMOTO';
 assert.ok(!excluded.has(sourceBrand+':'+r.source.row),'Red row imported');sourceRows.add(sourceBrand+':'+r.source.row);
 const p=byId.get(r.uid);assert.ok(p);assert.equal(JSON.parse(p.gallery)[0].img,r.mainPhoto);
 assert.equal(p.price===null?null:Number(p.price),r.price);assert.equal(p.brand,r.brand);
 for(const photo of r.additionalPhotos)assert.ok(photo.diskPath.includes('/На белом фоне/'));
}
assert.equal(sourceRows.size,87);
const {catalog}=require('./api/catalog');
assert.equal(catalog({}).total,data.products.length);
const ids=new Set();for(let slice=1;slice<=Math.ceil(data.products.length/36);slice++)for(const p of catalog({slice}).products)ids.add(p.uid);assert.equal(ids.size,data.products.length);
for(const part of data.parts)assert.ok(catalog({storepartuid:String(part.uid)}).total>0);
assert.ok(catalog({'filters[brand][0]':'YOKOMOTO','filters[brand][1]':'BONATEK'}).products.every(p=>['YOKOMOTO','BONATEK'].includes(p.brand)));
assert.equal(catalog({storepartuid:String(data.partuid),'filters[storepartuid][0]':'Пускозарядные устройства'}).total,4);
const charging=catalog({'filters[brand][0]':'YOKOMOTO','filters[equipment_type][0]':'Пускозарядное устройство'});assert.equal(charging.total,4);
for(const p of catalog({'filters[voltage][0]':'220 В'}).products)assert.ok(p.voltage.includes('220 В'));
for(const p of catalog({'filters[nominal_power][0]':'5 кВт'}).products)assert.equal(p.nominal_power,'5 кВт');
for(const alias of ['544983720072-motopompa-yokomoto-50cx','880477745052-generator-yokomoto-4000-ix'])assert.ok(fs.existsSync('public/catalog/tproduct/'+alias+'.html'));
console.log(JSON.stringify({products:data.products.length,photos,descriptions,categories:data.parts.length,added:report.addedProducts,updated:report.updatedCards,skippedRed:excluded.size,checks:'passed'},null,2));
