"""Convert a downloaded Motion Atlas run/bundle into JsonUtility-friendly Unity data.
Usage: python convert_for_unity.py downloaded.json
Unity uses x=Unreal Y/100, y=Unreal Z/100, z=Unreal X/100.
"""
import json,sys
from pathlib import Path
def pos(p):return dict(x=p[0],y=p[1],z=-p[2])
def convert(r):
 tracks=[]
 for key in ['left','right','vl','vr','head']:
  parts=[];part=[]
  for p in r['tracks'][key]:
   if p is None:
    if len(part)>1:parts.append(part)
    part=[]
   else:part.append(pos(p))
  if len(part)>1:parts.append(part)
  for part in parts:tracks.append(dict(name=key,points=part,dashed=key in ['vl','vr']))
 return dict(id=r['id'],coordinateSystem='Unity metres: x=UnrealY/100, y=UnrealZ/100, z=UnrealX/100',tracks=tracks,targets=[dict(name=f"T{q['id']:02}",position=pos(q['position'])) for q in r['targets']],events=[dict(name=e['title'],position=pos(e['position']),time=e['t'],body=e.get('text','')) for e in r['events']])
if __name__=='__main__':
 p=Path(sys.argv[1]);d=json.loads(p.read_text());runs=d.get('runs',[d]) if d.get('schema')=='vr-motion-atlas-bundle/1' else [d]
 for r in runs:
  out=p.with_name(r['id']+'_unity.json');out.write_text(json.dumps(convert(r),indent=2));print(out)
