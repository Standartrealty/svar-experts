import gzip
import concurrent.futures as cf, urllib.request as ur, urllib.parse as up, json, re, pathlib, hashlib, time, html
ROOT=pathlib.Path(__file__).resolve().parent; SRC=ROOT/'source'; OUT=ROOT/'public'; OUT.mkdir(exist_ok=True)
def fetch(url):
 for n in range(4):
  try:
   req=ur.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with ur.urlopen(req,timeout=60) as r:
    data=r.read()
    return gzip.decompress(data) if data[:2]==b'\x1f\x8b' else data
  except Exception:
   if n==3:raise
   time.sleep(n+1)
def pool(fn,seq,workers=8):
 with cf.ThreadPoolExecutor(max_workers=workers) as ex:return list(ex.map(fn,seq))
def get_slice(i):
 path=SRC/f'catalog-{i}.json'
 if not path.exists():path.write_bytes(fetch(f'https://store.tildaapi.com/api/getproductslist/?storepartuid=683635116312&recid=1556473581&getparts=true&getoptions=true&slice={i}'))
 return json.loads(path.read_text())
responses=pool(get_slice,range(1,11),4)
products={str(p['uid']):p for r in responses for p in r.get('products',[])}
assert len(products)==responses[0]['total'],(len(products),responses[0]['total'])
(SRC/'products.json').write_text(json.dumps(list(products.values()),ensure_ascii=False,indent=2))
print('PRODUCTS',len(products),flush=True)
urls=set(re.findall(r'<loc>(.*?)</loc>',(SRC/'sitemap.xml').read_text()))
urls={u.replace('http:','https:') for u in urls}
urls.update(p['url'].replace('http:','https:') for p in products.values())
# Include linked alternate slugs and internal pages.
for f in SRC.glob('*.html'):
 for u in re.findall(r'href=[\"\']([^\"\']+)',f.read_text()):
  u=html.unescape(u);p=up.urlsplit(u)
  if p.hostname in ['svar-experts.ru','svarexperts.ru'] and not p.query:urls.add('https://svar-experts.ru'+(p.path or '/'))
pagefiles={}
def page(u):
 p=up.urlsplit(u).path; name=p.strip('/') or 'index'; f=SRC/'pages'/(name+'.html'); f.parent.mkdir(parents=True,exist_ok=True)
 try:
  if not f.exists():f.write_bytes(fetch(u))
  return u,f
 except Exception as e:return u,str(e)
results=pool(page,sorted(urls))
errors={u:f for u,f in results if isinstance(f,str)}
pagefiles={u:f for u,f in results if not isinstance(f,str)}
print('PAGES',len(pagefiles),'ERRORS',errors,flush=True)
(SRC/'page-errors.json').write_text(json.dumps(errors,indent=2))
# Collect all static assets, including product galleries and inline backgrounds.
asset_re=re.compile(r'https?://(?:static|thb|optim|ws)\.tildacdn\.(?:com|net|pub|biz|one|info|ru)/[^\s\"\'<>\\)]+')
assets=set()
for f in pagefiles.values():assets.update(asset_re.findall(html.unescape(f.read_text())))
for p in products.values():
 for g in json.loads(p.get('gallery') or '[]'):assets.add(g['img'])
 for ed in p.get('editions',[]):
  if ed.get('img'):assets.add(ed['img'])
 assets.update(asset_re.findall(p.get('text','')+p.get('descr','')))
assets={u.rstrip(';},') for u in assets if not u.endswith('/')}
mapping={}; failures={}; texts={}
def asset(u):
 ext=pathlib.PurePosixPath(up.urlsplit(u).path).suffix
 if len(ext)>8:ext=''
 rel='assets/'+hashlib.sha256(u.encode()).hexdigest()[:24]+ext
 f=OUT/rel;f.parent.mkdir(exist_ok=True)
 try:
  if not f.exists():f.write_bytes(fetch(u))
  return u,rel,None
 except Exception as e:return u,rel,str(e)
for round in range(4):
 pending=assets-set(mapping)-set(failures)
 if not pending:break
 print('ASSET ROUND',round,len(pending),flush=True)
 for u,rel,e in pool(asset,sorted(pending),10):
  if e:failures[u]=e
  else:
   mapping[u]='/'+rel
   if rel.endswith(('.css','.js')):
    txt=(OUT/rel).read_text(errors='replace');texts[u]=txt
    assets.update(asset_re.findall(txt))
    if rel.endswith('.css'):
     for ref in re.findall(r'url\([\"\']?([^\)\"\']+)',txt):
      if not ref.startswith('data:'):assets.add(up.urljoin(u,ref))
print('ASSETS',len(mapping),'FAILURES',len(failures),flush=True)
(SRC/'asset-map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2));(SRC/'asset-errors.json').write_text(json.dumps(failures,indent=2))
def rewrite(s):
 for u,local in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(u,local).replace(u.replace('&','&amp;'),local).replace(u.replace('/',r'\/'),local).replace(u.replace('/',r'\\/'),local)
 s=re.sub(r'https?://(?:svar-experts\.ru|svarexperts\.ru)(?=[/\"\'])','',s)
 return s
for u,f in pagefiles.items():
 p=up.urlsplit(u).path.strip('/'); target=OUT/(p+'.html' if p else 'index.html');target.parent.mkdir(parents=True,exist_ok=True)
 s=rewrite(f.read_text());s=s.replace('</head>','<script src="/migration-runtime.js"></script></head>',1);target.write_text(s)
for u,s in texts.items():
 if mapping[u].endswith('.css'):
  for ref in re.findall(r'url\([\"\']?([^\)\"\']+)',s):
   absolute=up.urljoin(u,ref)
   if absolute in mapping:s=s.replace(ref,mapping[absolute])
 (OUT/mapping[u].lstrip('/')).write_text(rewrite(s))
data=dict(responses[0]);data['products']=list(products.values());data['nextslice']=None
(OUT/'catalog-data.json').write_text(rewrite(json.dumps(data,ensure_ascii=False)))
(ROOT/'migration-report.json').write_text(json.dumps({'products':len(products),'declaredProducts':responses[0]['total'],'pages':len(pagefiles),'assets':len(mapping),'pageErrors':errors,'assetErrors':failures},ensure_ascii=False,indent=2))
print('DONE',flush=True)
