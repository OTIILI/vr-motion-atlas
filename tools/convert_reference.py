"""Convert the four author reference recordings, retaining source provenance.
Usage: python tools/convert_reference.py path/to/R1.zip
Requires numpy and scipy. Source ZIP is not copied into the public package.
"""
from pathlib import Path
import sys,json,zipfile,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist/data'
ORDER=['47A55D8948775299D41E00A53B378621','1451A1604B11D5B3718201B01EB8B6B8','4D47D0A84396F6625446B5956533E460','05E86BE948C00FDBEC685C8F79991A1E']
def decode(raw):
 s=raw.decode('utf-8-sig');i=0;dec=json.JSONDecoder();rows=[]
 while i<len(s):
  while i<len(s) and s[i].isspace():i+=1
  if i==len(s):break
  r,i=dec.raw_decode(s,i);rows.append(r)
 return rows

def xyz(d):return [d[k] for k in ('x','y','z')]
def vec(p):return [float(p[1]/100),float(p[2]/100),float(-p[0]/100)]
def main(path):
 OUT.mkdir(exist_ok=True);manifest=[];provenance=[];canonical=None
 with zipfile.ZipFile(path) as z:
  for index,guid in enumerate(ORDER,1):
   name=next(n for n in z.namelist() if Path(n).stem==guid);raw=z.read(name);r=decode(raw);alltime=60-np.array([d['timestamp'] for d in r]);start=max(0,np.flatnonzero(alltime>1e-6)[0]-1);ix=np.arange(start,len(r));ix=ix[np.r_[True,np.diff(alltime[ix])>1e-8]];t=alltime[ix];grid=np.arange(0,t[-1]+1e-6,.1)
   nearest=np.searchsorted(t,grid).clip(0,len(t)-1);before=(nearest-1).clip(0,len(t)-1);nearest=np.where(abs(t[before]-grid)<=abs(t[nearest]-grid),before,nearest);rawix=ix[nearest]
   hi=np.searchsorted(t,grid).clip(0,len(t)-1);lo=(hi-1).clip(0,len(t)-1);valid=(t[hi]-t[lo])<.25
   arrays={}
   for key,field in [('left','leftMotionControllerTransform'),('right','rightMotionControllerTransform'),('vl','leftVisibleHandTransform'),('vr','rightVisibleHandTransform'),('head','headTransform')]:
    arr=np.array([xyz(d[field]['translation']) for d in r]);arrays[key]=np.array([np.interp(grid,t,arr[ix,j]) for j in range(3)]).T
   for key in ['left','right','vl','vr']:valid&=np.linalg.norm(arrays[key]-arrays['head'],axis=1)<(200 if key in ['left','right'] else 600)
   tracks={key:[vec(p) if ok else None for p,ok in zip(a,valid)] for key,a in arrays.items()}
   q=np.array([[r[j]['headTransform']['rotation'][k] for k in ['x','y','z','w']] for j in rawix]);rot=Rotation.from_quat(q)
   directions={key:[vec(p*100) if ok else None for p,ok in zip(rot.apply(np.broadcast_to(axis,(len(grid),3))),valid)] for key,axis in [('forward',[1,0,0]),('right',[0,1,0]),('up',[0,0,1])]}
   targets=np.array([[xyz(p) for p in d['handInterActionTargetLocatiions']] for d in r]);initial=targets[0]
   if canonical is None:canonical=initial
   mapping=np.linalg.norm(initial[:,None,:]-canonical[None,:,:],axis=2).argmin(axis=1)+1
   assert len(set(mapping))==43 and np.max(np.linalg.norm(initial-canonical[mapping-1],axis=1))<.1
   attached=np.array([d['attachedTargetIndex'] for d in r],int);events=[];objects=[]
   for j,tid in enumerate(mapping):
    held=np.flatnonzero(attached==j);moving=np.flatnonzero(np.linalg.norm(targets[:,j]-initial[j],axis=1)>2)
    if not len(held) and not len(moving):continue
    a=int(held[0]) if len(held) else int(moving[0]);end=len(r)-1;oi=np.unique(np.r_[np.arange(max(a,start),end+1,6),end]);objects.append(dict(target=int(tid),outcome='unattributed',headTargetCm=float(np.linalg.norm(targets[a,j]-np.array(xyz(r[a]['headTransform']['translation'])))),points=[[max(0,float(alltime[k])),*vec(targets[k,j])] for k in oi]))
   for k in range(start,len(r)):
    now=attached[k];prev=attached[k-1] if k else -1
    if now!=prev:
     for j,typ in [(prev,'release'),(now,'grab')]:
      if j<0 or j>=43:continue
      tid=int(mapping[j]);events.append(dict(id=f'{typ}-{k}',type=typ,target=tid,t=max(0,float(alltime[k])),position=vec(targets[k,j]),title=f'T{tid:02}: logged {typ}',text='Raw attachment-index transition; not independently validated.'))
    if k and r[k]['objectsDroppedToTarget']>r[k-1]['objectsDroppedToTarget']:
     events.append(dict(id=f'counter-{k}',type='audit',target=None,t=max(0,float(alltime[k])),position=vec(arrays['head'][int(np.argmin(abs(grid-alltime[k])))]),title='Recorded goal-counter increment',text=f"Recorded counter increased to {r[k]['objectsDroppedToTarget']}. Target attribution has not been reconstructed for this example; marker is anchored at the head, not the goal."))
   limit=float(np.median([r[k]['progressionFactorLimit'] for k in ix]));condition={.15:1,.35:2,.65:3}[round(limit,2)];rid=f'R1-R{index}'
   data=dict(schema='vr-motion-atlas/1',id=rid,participant='R1',condition=condition,runIndex=index,repeat=index==4,limit=limit,score=r[-1]['totalScore'],duration=float(grid[-1]),sampleHz=10,times=grid.tolist(),tracks=tracks,headDirections=directions,headQuaternionUE=q.tolist(),headAnchor=next(p for p in tracks['head'] if p is not None),factor=np.interp(grid,t,[r[k]['progressionFactor'] for k in ix]).tolist(),targets=[dict(id=int(tid),position=vec(p)) for tid,p in zip(mapping,initial)],objects=objects,events=events,ratings={},sourceRole='author reference demonstration; not a study participant')
   (OUT/f'{rid}.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False));manifest.append({k:data[k] for k in ['id','participant','condition','runIndex','repeat','limit','score','duration']});provenance.append(dict(id=rid,source=name,sha256=hashlib.sha256(raw).hexdigest(),rawFrames=len(r),timedFrames=len(ix),validDisplayFrames=int(valid.sum()),displayFrames=len(grid),rawFinalGoalCount=r[-1]['objectsDroppedToTarget']))
 (OUT/'manifest.json').write_text(json.dumps(dict(schema='vr-motion-atlas/1',coordinateSystem='Metres: x=Unreal Y/100, y=Unreal Z/100, z=-Unreal X/100. No yaw alignment.',sampling='10Hz author reference overview; no participant recordings or questionnaire ratings.',runs=manifest,targets=data['targets'])))
 (ROOT/'examples/author-reference-results/conversion_provenance.json').write_text(json.dumps(provenance,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':main(sys.argv[1])
