const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const {catalog}=require('./api/catalog');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.svg':'image/svg+xml','.webp':'image/webp','.woff2':'font/woff2','.ico':'image/x-icon'};
http.createServer((req,res)=>{
 const u=new URL(req.url,'http://localhost');
 if(u.pathname==='/api/catalog') {let body='';req.on('data',d=>body+=d);req.on('end',()=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(catalog(Object.fromEntries(u.searchParams),body)));});return;}
 let file=path.join(__dirname,'public',decodeURIComponent(u.pathname));
 if(u.pathname==='/')file=path.join(file,'index.html');
 if((!fs.existsSync(file)||fs.statSync(file).isDirectory())&&!path.extname(file))file+='.html';
 if(!file.startsWith(path.join(__dirname,'public'))||!fs.existsSync(file)||fs.statSync(file).isDirectory()){res.writeHead(404);res.end('Not found');return;}
 res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
}).listen(4173,'127.0.0.1',()=>console.log('http://127.0.0.1:4173'));
