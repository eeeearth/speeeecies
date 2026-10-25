#!/usr/bin/env python3
"""Discover animal species keys with country-level open-licence GBIF observations.

Set SPEEEECIES_WAVE_SCRATCH to a directory on the bulk disk. Responses are
cached there. Run serially and do not treat raw leads as publishable issues.
"""
import collections,json,os,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRATCH=Path(os.environ['SPEEEECIES_WAVE_SCRATCH'])
SCRATCH.mkdir(parents=True, exist_ok=True)
manifest=json.loads((ROOT/'docs/species-backlog-2026-10.json').read_text())
regions={r['region']:r['continent'] for r in manifest['records']}
regions.update({
 'CI':'africa','CM':'africa','ET':'africa','MG':'africa','NG':'africa','ZW':'africa',
 'CN':'asia','ID':'asia','KR':'asia','NP':'asia','PH':'asia','VN':'asia',
 'GR':'europe','HU':'europe','NO':'europe','PT':'europe','RO':'europe','SE':'europe',
 'GT':'north-america','PA':'north-america',
 'BO':'south-america','VE':'south-america','UY':'south-america',
 'PG':'oceania','FJ':'oceania',
 'AO':'africa','BJ':'africa','BW':'africa','GH':'africa','MW':'africa','MZ':'africa','NA':'africa','RW':'africa','SN':'africa','UG':'africa',
 'BD':'asia','BT':'asia','KH':'asia','LA':'asia','MM':'asia','MY':'asia','PK':'asia','TH':'asia',
 'BG':'europe','DK':'europe','IE':'europe','RS':'europe',
 'CR':'north-america','CU':'north-america','DO':'north-america','NI':'north-america',
 'EC':'south-america','GY':'south-america','PY':'south-america','SR':'south-america',
 'NC':'oceania','NZ':'oceania',
 'CD':'africa','GA':'africa','GM':'africa','GN':'africa','LR':'africa','SL':'africa','ZM':'africa',
 'LK':'asia','MN':'asia',
 'BZ':'north-america','HN':'north-america','JM':'north-america','SV':'north-america','TT':'north-america',
 'GF':'south-america',
 'SB':'oceania','VU':'oceania',
})
# GBIF places squamates in class Squamata, within the traditional reptile group.
# This discovery pass covers squamates; later passes can add turtle/crocodilian classes.
GROUPS={'Aves':212,'Mammalia':359,'Reptilia':11592253,'Amphibia':131}
HEADER={'User-Agent':'speeeecies backlog screening/1.0 (https://github.com/eeeearth/speeeecies)'}
def load(url,path):
 if path.exists():return json.loads(path.read_text())
 for attempt in range(5):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=HEADER),timeout=45) as r:d=json.load(r)
   path.write_text(json.dumps(d,separators=(',',':')))
   return d
  except Exception as e:
   print('retry',url,e,flush=True)
   time.sleep(3*(attempt+1))
 raise RuntimeError(url)
all_hits={}
for index,(country,continent) in enumerate(sorted(regions.items())):
 for group,key in GROUPS.items():
  params={'country':country,'taxonKey':key,'license':['CC0_1_0','CC_BY_4_0'],'basisOfRecord':'HUMAN_OBSERVATION','occurrenceStatus':'PRESENT','hasGeospatialIssue':'false','month':'1,12','limit':0,'facet':'speciesKey','facetLimit':2000,'facetMincount':300}
  url='https://api.gbif.org/v1/occurrence/search?'+urllib.parse.urlencode(params,doseq=True)
  path=SCRATCH/f'facet2-{country}-{group}.json'
  d=load(url,path)
  if not d.get('facets'):raise RuntimeError('no facet '+url)
  for hit in d['facets'][0]['counts']:
   gbif=int(hit['name']); count=int(hit['count'])
   item=all_hits.setdefault(gbif,{'gbif_usage_key':gbif,'group':group,'countries':[]})
   if item['group']!=group:raise RuntimeError('group collision')
   item['countries'].append({'region':country,'continent':continent,'count':count,'discovery_url':url})
 print('country',index+1,'/',len(regions),country,'unique',len(all_hits),flush=True)
for item in all_hits.values():
 item['countries'].sort(key=lambda x:(-x['count'],x['region']))
 item['best']=item['countries'][0]
(SCRATCH/'discovered.json').write_text(json.dumps(sorted(all_hits.values(),key=lambda x:x['gbif_usage_key']),separators=(',',':')))
print('complete unique',len(all_hits),flush=True)
print('groups',dict(collections.Counter(x['group'] for x in all_hits.values())),flush=True)
print('continents',dict(collections.Counter(x['best']['continent'] for x in all_hits.values())),flush=True)
