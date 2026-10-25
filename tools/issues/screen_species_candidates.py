#!/usr/bin/env python3
"""Screen GBIF leads against current repo/issues/PRs and exact iNaturalist taxa.

Set SPEEEECIES_WAVE_SCRATCH to a bulk-disk directory holding discovered.json,
issues-existing.json and open-prs.json. Honors iNaturalist's roughly 1/s API
recommendation; state and provider responses are resumable. The accepted list
is an issue research lead, not a finished species record.
"""
import collections,hashlib,json,os,re,time,urllib.parse,urllib.request
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRATCH=Path(os.environ['SPEEEECIES_WAVE_SCRATCH'])
UA={'User-Agent':'speeeecies backlog screening/1.0 (https://github.com/eeeearth/speeeecies)'}
TARGET=int(os.environ.get('SPEEEECIES_WAVE_TARGET', '720'))
WEIGHTS=['Aves']*6+['Mammalia']*2+['Reptilia','Amphibia']
GROUPS=['Aves','Mammalia','Reptilia','Amphibia']
REPTILE_CLASSES={'Squamata','Testudines','Crocodylia','Rhynchocephalia'}
CONTINENTS=['europe','north-america','south-america','africa','asia','oceania']
# The earlier manifest uses continent labels; inspect and normalize them here.
source=json.loads(Path(os.environ.get('SPEEEECIES_WAVE_DISCOVERED', str(SCRATCH/'discovered.json'))).read_text())
reserve_source=isinstance(source, dict)
if reserve_source:
    if 'records' not in source:
        raise ValueError('Reserve source needs records')
    requested_batch=os.environ.get('SPEEEECIES_WAVE_BATCH')
    source=[x for x in source['records'] if requested_batch is None or str(x['later_batch'])==requested_batch]
    # Existing reptile reserve keys came from GBIF class Squamata.
    taxon_keys={'Aves':212,'Mammalia':359,'Reptilia':11592253,'Amphibia':131}
    allhits=[]
    for x in source:
        count=x.get('month_bearing_count') or x.get('gbif_country_month_bearing_count')
        params={'country':x['region'],'taxonKey':taxon_keys[x['group']],
                'license':['CC0_1_0','CC_BY_4_0'],'basisOfRecord':'HUMAN_OBSERVATION',
                'occurrenceStatus':'PRESENT','hasGeospatialIssue':'false','month':'1,12',
                'limit':0,'facet':'speciesKey','facetLimit':2000,'facetMincount':300}
        best={'region':x['region'],'continent':x['continent'],
              'count':count,
              'discovery_url':'https://api.gbif.org/v1/occurrence/search?'+urllib.parse.urlencode(params,doseq=True)}
        allhits.append({'gbif_usage_key':x['gbif_usage_key'],'group':x['group'],
                        'best':best,'countries':[best]})
else:
    allhits=source
print('discovered',len(allhits),'continents',collections.Counter(x['best']['continent'] for x in allhits),flush=True)
issues=json.loads((SCRATCH/'issues-existing.json').read_text())
prs=json.loads((SCRATCH/'open-prs.json').read_text())
old=json.loads((ROOT/'docs/species-backlog-2026-10.json').read_text())['records']
exclude_names=set()
exclude_keys={x['gbif_usage_key'] for x in old}
prior=json.loads((ROOT/'docs/species-prior-taxa-2026-10.json').read_text())['issues']
for item in prior.values():
    exclude_keys.update(int(item[k]) for k in ('usageKey','acceptedUsageKey') if item.get(k))
exclude_inat={x['inat_taxon_id'] for x in old}
for issue in issues:
 match=re.search(r'\(([^()]+)\)\s*$',issue['title'])
 if match:exclude_names.add(match.group(1).strip().lower())
 for key in re.findall(r'GBIF usage key:\s*`?(\d+)',issue.get('body') or ''):exclude_keys.add(int(key))
 for key in re.findall(r'iNaturalist taxon ID:\s*`?(\d+)',issue.get('body') or ''):exclude_inat.add(int(key))
 for key, inat in re.findall(r'species-backlog:[^:\s]+:(\d+):(\d+)', issue.get('body') or ''):
  exclude_keys.add(int(key));exclude_inat.add(int(inat))
for path in (ROOT/'species').glob('*/species.json'):
 d=json.loads(path.read_text());exclude_names.add(d['id'].lower());exclude_keys.add(d['external']['gbif_usage_key']);exclude_inat.add(d['external']['inat_taxon_id'])
for pr in prs:
 for file in pr['files']:
  name=file['path']
  if name.startswith('species/') and name.endswith('/species.json'):
   exclude_names.add(name.split('/')[1].replace('-',' '))
# Reserve remote branch species slugs as well.
import subprocess
branches=subprocess.check_output(['git','branch','-r','--no-color'],cwd=ROOT,text=True)
for match in re.finditer(r'species-\d+-([a-z0-9-]+)',branches):exclude_names.add(match.group(1).replace('-',' '))
print('excluded names',len(exclude_names),'keys',len(exclude_keys),'iNat',len(exclude_inat),flush=True)
bybucket=collections.defaultdict(list)
for hit in allhits:
 if hit['gbif_usage_key'] in exclude_keys:continue
 c=hit['best']['continent']; g=hit['group']
 bybucket[(c,g)].append(hit)
for bucket,values in bybucket.items():
 values.sort(key=lambda x:(-x['best']['count'],-len(x['countries']),x['gbif_usage_key']))
print('buckets',[(str(k),len(v)) for k,v in sorted(bybucket.items())],flush=True)
# Sweep groups in a 6:2:1:1 rhythm and rotate continents. Every key appears once.
ordered=[];seen=set()
while True:
 moved=False
 for group in WEIGHTS:
  for continent in CONTINENTS:
   bucket=bybucket[(continent,group)]
   while bucket and bucket[0]['gbif_usage_key'] in seen:bucket.pop(0)
   if bucket:
    x=bucket.pop(0);seen.add(x['gbif_usage_key']);ordered.append(x);moved=True
 if not moved:break
print('ordered',len(ordered),flush=True)
statepath=SCRATCH/'screen-progress.json'
input_files=[Path(os.environ.get('SPEEEECIES_WAVE_DISCOVERED', str(SCRATCH/'discovered.json'))),
             SCRATCH/'issues-existing.json', SCRATCH/'open-prs.json']
input_digest=hashlib.sha256(b''.join(path.read_bytes() for path in input_files)).hexdigest()
state=json.loads(statepath.read_text()) if statepath.exists() else {'screened':0,'accepted':[],'reasons':{},'input_digest':input_digest}
if state.get('input_digest') != input_digest:
    raise ValueError('Screening inputs changed after the run began; use a new scratch directory to reconcile GitHub and restart safely.')
orderpath=SCRATCH/'screened-order.json'
ordered_keys=[x['gbif_usage_key'] for x in ordered]
if orderpath.exists() and json.loads(orderpath.read_text()) != ordered_keys:
    raise ValueError('Screened order changed after the run began; use a new scratch directory.')
orderpath.write_text(json.dumps(ordered_keys))
accepted=state['accepted'];reasons=collections.Counter(state['reasons']);inat_used=exclude_inat|{x['inat_taxon_id'] for x in accepted};name_used=exclude_names|{x['scientific_name'].lower() for x in accepted}
def save():
 state['accepted']=accepted;state['reasons']=dict(reasons)
 temp=statepath.with_suffix('.part');temp.write_text(json.dumps(state,separators=(',',':')));temp.replace(statepath)
def get(url,path,delay=0):
 if path.exists():return json.loads(path.read_text())
 for attempt in range(5):
  try:
   if delay:time.sleep(delay)
   with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30) as r:d=json.load(r)
   path.write_text(json.dumps(d,separators=(',',':')))
   return d
  except Exception as e:
   print('retry',attempt,url,e,flush=True);time.sleep(5*(attempt+1))
 raise RuntimeError(url)
last_inat=0.0
for i in range(state['screened'],len(ordered)):
 hit=ordered[i];key=hit['gbif_usage_key'];state['screened']=i+1
 gbif=get(f'https://api.gbif.org/v1/species/{key}',SCRATCH/f'gbif-{key}.json')
 name=gbif.get('canonicalName','').strip()
 class_matches=(gbif.get('class')==hit['group'] or
                (hit['group']=='Reptilia' and gbif.get('class') in REPTILE_CLASSES))
 if gbif.get('rank')!='SPECIES' or gbif.get('taxonomicStatus')!='ACCEPTED' or gbif.get('kingdom')!='Animalia' or not class_matches:
  reasons['taxon']+=1
 elif not re.fullmatch(r'[A-Z][a-zA-Z-]+ [a-z][a-zA-Z-]+',name):
  reasons['nameformat']+=1
 elif name.lower() in name_used:
  reasons['existing']+=1
 # These fully aquatic or marine-dependent groups are outside the current scene format.
 elif gbif.get('order') in {'Cetacea','Sirenia'} or gbif.get('family') in {'Phocidae','Otariidae','Odobenidae'}:
  reasons['marine_mammal']+=1
 elif name in {'Felis catus','Canis familiaris','Bos taurus','Bos frontalis',
              'Bos grunniens','Bubalus bubalis','Capra hircus','Ovis aries',
              'Camelus dromedarius','Camelus bactrianus','Lama glama',
              'Vicugna pacos','Equus asinus','Equus caballus',
              'Cavia porcellus','Gallus gallus domesticus'}:
  reasons['domestic']+=1
 else:
  if reserve_source:
   params={'country':hit['best']['region'],'speciesKey':key,
           'license':['CC0_1_0','CC_BY_4_0'],'basisOfRecord':'HUMAN_OBSERVATION',
           'occurrenceStatus':'PRESENT','hasGeospatialIssue':'false',
           'month':'1,12','limit':0}
   observation_url='https://api.gbif.org/v1/occurrence/search?'+urllib.parse.urlencode(params,doseq=True)
   observation=get(observation_url,SCRATCH/f'occurrence-{key}.json')
   if int(observation.get('count',0))<300:
    reasons['low_observations']+=1
    if len(accepted)%25==0 or i%25==0:save()
    continue
   hit['best']['count']=int(observation['count'])
   hit['best']['discovery_url']=observation_url
  url='https://api.inaturalist.org/v1/taxa?'+urllib.parse.urlencode({'q':name,'rank':'species','per_page':20})
  cache=SCRATCH/f'inat-{key}.json'
  fresh=not cache.exists()
  if fresh:
   elapsed=time.monotonic()-last_inat
   if elapsed<1.1:time.sleep(1.1-elapsed)
  d=get(url,cache)
  if fresh:last_inat=time.monotonic()
  matches=[x for x in d.get('results',[]) if x.get('name','').lower()==name.lower() and x.get('rank')=='species' and x.get('is_active') is True and x.get('extinct') is not True]
  if len(matches)!=1:reasons['inat_match']+=1
  elif matches[0]['id'] in inat_used:reasons['inat_duplicate']+=1
  else:
   taxon=matches[0];common=taxon.get('preferred_common_name') or gbif.get('vernacularName') or name
   if not isinstance(common,str) or len(common)>100:common=name
   common=' '.join(common.split())
   item={'scientific_name':name,'common_name':common.strip(),'slug':name.lower().replace(' ','-'),'gbif_usage_key':key,'inat_taxon_id':taxon['id'],'group':hit['group'],'order':gbif.get('order'),'family':gbif.get('family'),'continent':hit['best']['continent'],'region':hit['best']['region'],'gbif_country_month_bearing_count':hit['best']['count'],'gbif_discovery_url':hit['best']['discovery_url'],'screened_on_utc':datetime.now(timezone.utc).date().isoformat(),'candidate_countries':[{'region':x['region'],'count':x['count']} for x in hit['countries'][:5]]}
   accepted.append(item);inat_used.add(taxon['id']);name_used.add(name.lower())
 if len(accepted)%25==0 or i%25==0:save()
 if len(accepted)%25==0 and len(accepted)>0:print('screened',i+1,'accepted',len(accepted),'reasons',dict(reasons),flush=True)
 if len(accepted)>=TARGET:break
save()
print('COMPLETE screened',state['screened'],'accepted',len(accepted),'reasons',dict(reasons),flush=True)
if len(accepted)<TARGET:raise SystemExit('Insufficient screened candidates')
