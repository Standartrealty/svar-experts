const fs=require('node:fs'),path=require('node:path'),{spawn,execFileSync}=require('node:child_process');
async function main(){
 execFileSync('tar',['-xzf','source-bundle.tar.gz'],{stdio:'inherit'});
 const parts=fs.readdirSync('asset-bundle').filter(p=>p.startsWith('part-')).sort();
 if(!parts.length)throw new Error('Asset bundle missing');
 fs.mkdirSync('public/assets',{recursive:true});
 const tar=spawn('tar',['-xzf','-','-C','public'],{stdio:['pipe','inherit','inherit']});
 const done=new Promise((resolve,reject)=>{tar.on('close',code=>code===0?resolve():reject(new Error('tar exit '+code)));tar.on('error',reject);});
 for(const part of parts){for await(const chunk of fs.createReadStream(path.join('asset-bundle',part))){if(!tar.stdin.write(chunk))await new Promise(resolve=>tar.stdin.once('drain',resolve));}}
 tar.stdin.end();await done;
 console.log('Restored assets from '+parts.length+' archive parts');
 const domain=process.env.VERCEL_PROJECT_PRODUCTION_URL||process.env.VERCEL_URL;
 if(domain){
  function pages(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?pages(path.join(dir,e.name)):(e.name.endsWith('.html')?[path.join(dir,e.name)]:[]));}
  const urls=pages('public').map(p=>p.replace(/^public/, '').replace(/index\.html$/, '').replace(/\.html$/, ''));
  fs.writeFileSync('public/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls.map(p=>'<url><loc>https://'+domain+p+'</loc></url>').join('')+'</urlset>');
  fs.writeFileSync('public/robots.txt','User-agent: *\nAllow: /\nSitemap: https://'+domain+'/sitemap.xml\n');
 }
 require('./verify');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
