"""Import the approved retail rows and their anchored workbook photographs."""
import pathlib,json,copy,re,hashlib,html,collections,tarfile
from PIL import Image,ImageOps
from lxml import html as H
ROOT=pathlib.Path(__file__).resolve().parent.parent;BASE=ROOT/'imports/price-2026-11-06';PUB=ROOT/'public'
data=json.loads((BASE/'catalog-before.json').read_text());items=json.loads((BASE/'items.json').read_text());excluded=json.loads((BASE/'excluded.json').read_text());disk=json.loads((BASE/'disk-assets.json').read_text())
templatePath=BASE/'product-template.html'
if not templatePath.exists():templatePath.write_text((PUB/'catalog/tproduct/555753590802-generator-invertornii-yokomoto-13500-oix.html').read_text())
template=templatePath.read_text();oldUID='555753590802';oldURL='/catalog/tproduct/555753590802-generator-invertornii-yokomoto-13500-oix'
originalById={p['uid']:p for p in data['products']};parts={p['title']:p['uid'] for p in data['parts']};parts['Пускозарядные устройства']=978613820001
data['parts'].append({**copy.deepcopy(data['parts'][-1]),'uid':parts['Пускозарядные устройства'],'title':'Пускозарядные устройства','path':['Пускозарядные устройства'],'sort':1000600})
matches={4:[617098665202],8:[684665753182],9:[145360683372],10:[815113154422],11:[894134507812,132652608042],12:[839024238452],13:[507181555652],14:[671797514712],15:[722548626322],16:[716649314392],17:[480845949512],18:[482918122372],19:[556569360112],20:[630837845282],21:[668758205112],22:[880477745052],23:[397401941362],24:[873331241892],25:[570929739812],26:[741193952032],27:[714561959482],28:[555753590802],33:[544983720072],34:[285459678102],35:[387800444792],40:[552934231152],41:[532939956232],42:[849862588762],43:[231919706972],49:[497899835592,722332343502],50:[289129404822],55:[960072444362]}
codes={4:'ATS-1 220V',5:'ATS-1 INVERTER 220V',6:'ATS-18000IOE',7:'CARBURETOR',8:'3800E',9:'3800EB',10:'4000E',11:'4000EB',12:'6500EB',13:'6500EBW',14:'7500EBW',15:'8500EBW',16:'9500EBW',17:'9500-3EBW',18:'9500-3EBWS',19:'13000EBW',20:'1500I',21:'4000I',22:'4000IX',23:'4000OI',24:'4000OIX',25:'6800OIX',26:'8800OIX',27:'9800OIX',28:'13500OIX',29:'18000OIX',33:'50CX',34:'80CX',35:'100CX',40:'AC-24/220',41:'AC-50/260',42:'AC-50/380',43:'AC-100/400',44:'W-0.36/8 100L',49:'AC-200/750',50:'AC-300/1100',51:'V-0.25/8-100L',52:'750Q-10L',54:'ACN-24/220',55:'ACN-50/280',57:'750W3-100L',58:'SYW1680 4-200L',59:'SY-SC-3KW',60:'SY-SC-4KW',81:'CUT-100 DC',82:'Ф6 PRO',83:'Ф9 VIZION',84:'Ф9 ULTIMA',85:'Ф10 ULTIMA',87:'MAD-30',88:'MAD-50',89:'BNC-500',90:'SUN-650-1'}
trans=str.maketrans(dict(zip('АВЕКМНОРСТХавекмнорстх','ABEKMHOPCTXabekmhopctx')))
def norm(s):
 s=s.upper().translate(trans);s=re.sub(r'\([^)]*\)','',s);s=s.replace('YOKOMOTO','').replace('BONATEK','').replace('VOLTBERRY','');s=re.sub(r'(\d+)\s*KVA',lambda m:str(int(m[1])*1000)+'VA',s);s=re.sub('[^A-ZА-Я0-9]','',s)
 if s.endswith('100L') or s.endswith('200L') or s.endswith('10L'):s=s[:-1]
 return s.replace('V55000IEK','V5500IEK').replace('V65000IEK','V6500IEK').replace('CUT100DC','CUT100')
def equipment(title,text=''):
 t=(title+' '+text).lower()
 if 'маска' in title.lower():return 'Сварочная маска'
 if 'плазм' in title.lower() or 'cut-100' in title.lower():return 'Плазморез'
 if 'пускозаряд' in title.lower():return 'Пускозарядное устройство'
 if 'карбюратор' in title.lower():return 'Карбюратор'
 if 'блок автоматики' in title.lower():return 'Блок автоматики ATS'
 if 'компрессор' in title.lower():return 'Винтовой компрессор' if 'винтовой' in t else ('Безмасляный компрессор' if 'безмасл' in t else 'Масляный компрессор')
 if 'помпа' in title.lower():return 'Мотопомпа'
 if 'стабилизатор' in title.lower():
  for word in ['Релейный','Тиристорный','Инверторный','Электромеханический']:
   if word.lower()[:7] in text.lower():return word+' стабилизатор'
  return 'Стабилизатор напряжения'
 if 'генератор' in title.lower():return 'Инверторный генератор' if 'инвертор' in title.lower() or 'инветор' in title.lower() else ('Дизельный генератор' if 'дизель' in title.lower() else 'Бензиновый генератор')
 return 'Сварочный аппарат'
def attributes(p):
 text=re.sub('<[^>]+>',' ',p.get('text',''));title=p['title'];p['equipment_type']=equipment(title,text)
 m=re.search(r'(?:Напряжение(?:\s*,?\s*В)?|Нпряжение)\s*[:–—-]?\s*(\d{2,3}(?:\s*[/–-]\s*\d{2,3})?)',html.unescape(text),re.I)
 volts=re.findall(r'\d+',m[1]) if m else re.findall(r'(?<!\d)(12|24|220|230|380|400)\s*В\b',title+' '+text,re.I)
 p['voltage']=sorted(set(v+' В' for v in volts))
 m=re.search(r'(?:Ном\.?\s*мощность|Номинальная\s+мощность)\s*(?:,\s*кВт)?\s*[:–—-]?\s*(\d+(?:[.,]\d+)?)\s*кВт',text,re.I)
 if not m:m=re.search(r'(?:Номинальная\s+мощность)\s*,?\s*кВт\s*[:–—-]?\s*(\d+(?:[.,]\d+)?)',text,re.I)
 if m:p['nominal_power']=m[1].replace('.',',')+' кВт'
 else:
  m=re.search(r'(\d+)\s*Вт\s*\(номинальн',text,re.I);p['nominal_power']=(str(int(m[1])/1000).rstrip('0').rstrip('.').replace('.',',')+' кВт') if m else ''
for p in data['products']:attributes(p)
def make_main(it):
 im=ImageOps.exif_transpose(Image.open(it['mainOriginal'])).convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);im=bg.convert('RGB')
 from io import BytesIO
 buf=BytesIO();im.save(buf,'WEBP',quality=95,method=5);content=buf.getvalue();name='price-20261106-'+hashlib.sha256(content).hexdigest()[:20]+'.webp';(PUB/'assets'/name).write_bytes(content);return '/assets/'+name
def additional(it,code,kind):
 brand=it['brand'];section=it['section']
 folder=('Генераторы '+('YOKOMOTO' if brand=='YOKOMOTO' else brand.title()))
 if section=='Компрессоры':folder='Компрессора YOKOMOTO'
 if section=='Мотопомпы':folder='Мотопомпы YOKOMOTO'
 if section=='Стабилизаторы' or kind.endswith('стабилизатор') or kind=='Стабилизатор напряжения':folder='Стабилизаторы '+brand.title()
 if brand=='BONATEK' and 'стабилизатор' in it['title'].lower():folder='Стабилизаторы Bonatek'
 if brand=='VOLTBERRY' and 'стабилизатор' in it['title'].lower():folder='Стабилизаторы Voltberry'
 if kind=='Плазморез':folder='Плазморезы YOKOMOTO'
 if kind in ['Блок автоматики ATS','Карбюратор','Сварочная маска','Пускозарядное устройство']:return []
 candidates=[x for x in disk if x['path'].split('/')[1].casefold()==folder.casefold()]
 exact=[x for x in candidates if norm(pathlib.Path(x['name']).stem)==norm(code)]
 # The workbook author explicitly allows shared photos within a brand/equipment family.
 shared=[]
 if not exact:
  preferred=[]
  if kind=='Бензиновый генератор' and brand=='YOKOMOTO':preferred=['Yokomoto 7500 8500 9500 EBW.jpg']
  if kind=='Инверторный генератор' and brand=='YOKOMOTO':preferred=['Yokomoto 4000 OIX.jpg']
  shared=[x for x in candidates if x['name'] in preferred]
 return [(x,False) for x in exact[:3]]+[(x,True) for x in shared[:2]]
letters={'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'}
def slug(s):return re.sub('[^a-z0-9]+','-',''.join(letters.get(c,c) for c in s.lower())).strip('-')[:150]
used=set(originalById);new=[];updated=[];records=[]
for it0 in items:
 variants=[copy.deepcopy(it0)]
 if it0['brand']=='YOKOMOTO' and it0['row']==4:
  variants=[{**copy.deepcopy(it0),'title':'Блок автоматики YOKOMOTO ATS-1, 220 В','priceRaw':'14300','variant':'ATS-1 220V'},{**copy.deepcopy(it0),'title':'Блок автоматики YOKOMOTO ATS-3, 380 В','priceRaw':'15400','variant':'ATS-3 380V'}]
 for it in variants:
  brand=it['brand'];row=it['row'];title=it['title'].replace('инветорный','инверторный');section=it['section']
  if 'маска сварочная' in title.lower():brand='SVAR EXPERT'
  if it['brand']=='BONATEK' and 'стабилизатор' in title.lower():section='Стабилизаторы'
  if section=='Сварочное оборудование и плазморезы':section='Сварочное оборудование'
  if 'помпа' in title.lower():title=re.sub(r'YOKOMOTO ПОМПА','Мотопомпа YOKOMOTO',title)
  code=(it.get('variant') or codes.get(row,'')) if it['brand']=='YOKOMOTO' else re.split(it['brand'],title,flags=re.I)[-1].strip(' ,')
  matchesIds=matches.get(row,[]) if it['brand']=='YOKOMOTO' and not it.get('variant','').startswith('ATS-3') else []
  if it['brand']=='BONATEK' and row==14:matchesIds=[632905379552]
  if it['brand']=='VOLTBERRY' and row==14:matchesIds=[437025297122]
  if not matchesIds:
   uid=100000000000+int(hashlib.sha256((brand+':'+title).encode()).hexdigest()[:12],16)%800000000000
   while uid in used:uid+=1
   used.add(uid);matchesIds=[uid]
  main=make_main(it);desc=it['description']
  if it.get('variant'):desc=re.sub(r'Напряжение\s*[-—:]?\s*220\s*/\s*380\s*В','Напряжение — '+('380 В' if 'ATS-3' in it['variant'] else '220 В'),desc)
  kind=equipment(title,desc);extras=additional(it,code,kind);gallery=[{'img':main}]+[{'img':x['asset'],'alt':('Общий вид серии ' if shared else 'Фото ')+brand+' '+kind} for x,shared in extras]
  for uid in matchesIds:
   existing=originalById.get(uid);p=existing if existing else copy.deepcopy(data['products'][0]);p['uid']=uid;p['title']=title;p['brand']=brand;p['sku']=code;p['text']=html.escape(desc).replace('\n','<br />') if desc else (existing.get('text','') if existing else '')
   p['price']=str(int(it['priceRaw'])) if re.fullmatch(r'\d+',it['priceRaw']) else None;p['priceold']='';p['descr']='';p['gallery']=json.dumps(gallery,ensure_ascii=False);p['partuids']=json.dumps([parts[section]])
   if not existing:p['url']='/catalog/tproduct/'+str(uid)+'-'+slug(title);p['externalid']='price-2026-11-06-'+str(uid);p['sort']=0
   p['editions']=[{'uid':uid,'price':p['price'],'priceold':'','sku':code,'quantity':'','img':main}];p['characteristics']=[];p['json_options']='';p['importSource']={'batch':'price-2026-11-06','file':it['sourceFile'],'sheet':it['sourceSheet'],'row':row};attributes(p)
   if existing:updated.append(uid)
   else:new.append(copy.deepcopy(p))
   records.append({'uid':uid,'brand':brand,'title':title,'action':'updated' if existing else 'added','source':p['importSource'],'category':section,'equipmentType':p['equipment_type'],'price':int(p['price']) if p['price'] is not None else None,'mainPhoto':main,'mainPhotoWorkbookMedia':pathlib.Path(it['mainOriginal']).name,'additionalPhotos':[{'asset':x['asset'],'diskPath':x['path'],'sharedSeries':shared} for x,shared in extras]})
data['products']=new+data['products'];data['total']=len(data['products']);data['nextslice']=2
# Recompute filter options from the actual resulting catalog.
def values(field):
 c=collections.Counter()
 for p in data['products']:
  for value in set(p.get(field,[]) if isinstance(p.get(field),list) else [p.get(field,'')]):
   if value:c[value]+=1
 return [{'value':v,'count':n} for v,n in sorted(c.items())]
data['filters']['filters']=[{'id':4073842,'label':'Бренд','control':'select','type':'product','name':'brand','values':values('brand')},{'id':4073843,'label':'Тип оборудования','control':'select','type':'product','name':'equipment_type','values':values('equipment_type')},{'id':4073844,'label':'Напряжение','control':'select','type':'product','name':'voltage','values':values('voltage')},{'id':4073845,'label':'Номинальная мощность','control':'select','type':'product','name':'nominal_power','values':values('nominal_power')}]
(PUB/'catalog-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
def render(p):
 s=template.replace(oldUID,str(p['uid'])).replace(oldURL.replace(oldUID,str(p['uid'])),p['url']);start=s.index('var product = ')+len('var product = ');obj,end=json.JSONDecoder().raw_decode(s[start:]);obj.update(p);obj['gallery']=json.loads(p['gallery']);obj['partuids']=json.loads(p['partuids']);obj['price']=str(p['price']) if p['price'] is not None else '';obj['properties']=[]
 for ed in obj['editions']:ed['price']=str(p['price']) if p['price'] is not None else ''
 s=s[:start]+json.dumps(obj,ensure_ascii=False).replace('<','\\u003c')+s[start+end:];doc=H.document_fromstring(s)
 def cls(name):return doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," '+name+' ")]')
 doc.find('head/title').text=p['title']+' — '+p['brand']
 for el in cls('js-product-name'):el.text=p['title']
 for el in cls('js-product-brand'):el.text=p['brand']
 for el in cls('js-product-sku'):el.text=p['sku']
 for el in cls('js-store-prod-all-text'):
  for child in list(el):el.remove(child)
  el.text=''
  for frag in H.fragments_fromstring(p['text'] or ''):
   if isinstance(frag,str):el.text=(el.text or '')+frag
   else:el.append(frag)
 for el in cls('js-product-price'):
  el.text=format(int(p['price']),',').replace(',',' ') if p['price'] is not None else '';el.set('data-product-price-def',str(p['price'] or ''));el.set('data-product-price-def-str',str(p['price'] or ''))
 if p['price'] is not None:
  for el in cls('js-store-prod-price'):el.attrib.pop('style',None)
  for el in doc.xpath('//*[@itemprop="offers"]'):el.attrib.pop('style',None)
 for el in doc.xpath('//meta[@itemprop="price"]'):el.set('content',str(p['price'] or ''))
 for el in doc.xpath('//meta[@itemprop="image"] | //meta[@property="og:image"]'):el.set('content',json.loads(p['gallery'])[0]['img'])
 for el in doc.xpath('//meta[@property="og:title"]'):el.set('content',p['title'])
 for el in doc.xpath('//meta[@property="og:url"]'):el.set('content','https://svar-experts.vercel.app'+p['url'])
 for el in doc.xpath('//link[@rel="canonical"]'):el.set('href','https://svar-experts.vercel.app'+p['url'])
 for el in doc.xpath('//meta[@name="description"] | //meta[@property="og:description"]'):el.set('content',re.sub('<[^>]*>',' ',p['text'])[:240] or p['title'])
 output=H.tostring(doc,encoding='unicode',method='html')
 # libxml's HTML4 serializer closes anchors before tables. Restore Tilda's HTML5 buy button.
 output=re.sub(r'(<a\b[^>]*class="[^"]*\bt-store__prod-popup__btn\b[^"]*"[^>]*>)\s*</a>\s*(<table\b.*?</table>)',r'\1\2</a>',output,flags=re.S)
 return '<!DOCTYPE html>\n'+output
for p in data['products']:
 if p['uid'] in updated or any(x['uid']==p['uid'] for x in new):
  content=render(p);routes=list((PUB/'catalog/tproduct').glob(str(p['uid'])+'-*.html')) or [PUB/(p['url'].lstrip('/')+'.html')]
  for route in routes:route.write_text(content)
report={'batch':'price-2026-11-06','includedRows':len(items),'excludedRedRows':len(excluded),'addedProducts':len(new),'updatedCards':len(updated),'totalProducts':len(data['products']),'retailPriceColumn':'МРЦ','records':records,'excluded':[{'brand':p['brand'],'row':p['row'],'title':p['title'],'reason':'Красная заливка товарной строки'} for p in excluded],'photosPublicShare':'https://disk.yandex.ru/d/O47DsSmSSn7k6Q','originalRedProductsAlreadyOnSite':'Existing unrelated cards were preserved and not updated by this import.'}
report['sourceGaps']=[{'file':it['sourceFile'],'sheet':it['sourceSheet'],'row':it['row'],'title':it['title'],'missing':(['characteristics'] if not it['description'] else [])+(['retailPrice'] if not it['priceRaw'] else [])} for it in items if not it['description'] or not it['priceRaw']]
(ROOT/'source/catalog-import-2026-11-06.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print({k:v for k,v in report.items() if k not in ['records','excluded']})
