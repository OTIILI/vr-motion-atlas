import os
from pathlib import Path
import numpy as np,pandas as pd,json
BASE=Path(os.environ.get('ATLAS_ANALYSIS_ROOT', 'private-analysis'));OUT=Path(__file__).resolve().parents[1]/'dist/data';OUT.mkdir(exist_ok=True)
E=pd.read_csv(BASE/'event-work/results/events.csv');P=pd.read_csv(BASE/'event-work/results/phase_timeline.csv');G=pd.read_csv(BASE/'event-work/results/goal_audit.csv');ratings=pd.read_csv(BASE/'subjective-work/subjective_ratings.csv').set_index('participant');inv=pd.read_csv(BASE/'subjective-work/run_final_scores.csv');manifest=[]
def clean(x):
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 if isinstance(x,(np.integer,)):return int(x)
 if isinstance(x,(np.floating,)):return round(float(x),4) if np.isfinite(x) else None
 if isinstance(x,float):return round(x,4) if np.isfinite(x) else None
 if isinstance(x,(np.bool_,)):return bool(x)
 return x
def vec(q):return [float(q[1]/100),float(q[2]/100),float(-q[0]/100)]
for k,r in inv.iterrows():
 d=dict(np.load(BASE/'event-work/cache'/r.file.replace('.ndjson','.npz')));t=60-d['ts'];ix=np.flatnonzero(t>1e-6);start=max(0,ix[0]-1);ix=np.arange(start,len(t));tt=t[ix];unique=np.r_[True,np.diff(tt)>1e-8];ix=ix[unique];tt=t[ix]
 # 10 Hz display sampling; raw-frame event positions retained separately.
 grid=np.arange(0,float(tt[-1])+.0001,.1);samples={};valid=np.ones(len(grid),dtype=bool)
 for key in ['left','right','vl','vr','head']:
  arr=np.array([np.interp(grid,tt,d[key][ix,j]) for j in range(3)]).T;samples[key]=arr
 for key in ['left','right','vl','vr']:valid&=np.linalg.norm(samples[key]-samples['head'],axis=1)<(200 if key in ['left','right'] else 600)
 hi=np.searchsorted(tt,grid,side='left').clip(0,len(tt)-1);lo=(hi-1).clip(0,len(tt)-1);valid&=(tt[hi]-tt[lo])<.25
 tracks={key:[vec(q) if good else None for q,good in zip(arr,valid)] for key,arr in samples.items()}
 events=[];objects=[]
 for e in E[E.file==r.file].itertuples():
  j=int(e.raw_index);f=int(e.first_frame);rel=int(e.release_frame);ph=P[(P.file==r.file)&(P.target==e.target)].iloc[0];end=min(len(t)-1,int(ph.terminal_frame) if pd.notna(ph.terminal_frame) else len(t)-1);end=max(end,rel)
  q0=d['targets'][max(0,f-1),j];base=dict(target=int(e.target),outcome=e.outcome,pickupClass=e.pickup_class,headTargetCm=e.head_target_cm,holdSeconds=e.hold_s,preclock=e.preclock,transportCm=e.max_displacement_cm,goalTentative=e.goal_new_tentative)
  if e.logged_attachment:events.append(dict(id=f'{e.target}-grab',type='grab',t=max(0,float(t[f])),position=vec(q0),title=f'T{e.target:02d}: logged attachment',text=('Attachment began before the countdown; duration is excluded from timed statistics.' if e.preclock else f'Logged attachment. Head–target distance ≈ {e.head_target_cm:.0f} cm; total logged hold {e.hold_s:.2f} s.'),**base))
  events.append(dict(id=f'{e.target}-release',type=('activation' if not e.logged_attachment else ('early' if e.short_fall else 'release')),t=max(0,float(t[rel])),position=vec(d['targets'][rel,j]),title=f'T{e.target:02d}: '+('displacement without logged attachment' if not e.logged_attachment else ('early-release/fall candidate' if e.short_fall else 'logged release')),text=('Target displacement without a logged attachment. Contact or another physical interaction cannot be ruled out; this is not a confirmed pickup.' if not e.logged_attachment else 'Attachment ≤0.3s, then ≥5cm fall within 0.5s. Candidate only; intentional release is not ruled out.' if e.short_fall else 'Final logged attachment end. A terminal outcome without attribution is not a confirmed miss.'),**base))
  if pd.notna(e.score_frame):
   sf=int(e.score_frame);events.append(dict(id=f'{e.target}-goal',type='goal',t=max(0,float(t[sf])),position=vec(d['targets'][sf,j]),title=f'T{e.target:02d}: '+('tentative goal attribution' if e.goal_new_tentative else 'original goal attribution'),text='Counter increment linked to this target by the provisional spatial/event audit. This is an attribution, not independently verified ground truth.',**base))
  # Object path from latest timed attachment context until terminal proxy.
  a=max(start,f);z=max(a,end);oi=np.unique(np.r_[np.arange(a,z+1,6),z]);objects.append(dict(target=int(e.target),points=[[max(0,float(t[f0])),*vec(d['targets'][f0,j])] for f0 in oi],**{k:v for k,v in base.items() if k!='target'}))
 # Explicit counter anomalies anchored near the last credited ball where available.
 for gg in G[(G.file==r.file)&G.old_unresolved].itertuples():
  f=int(gg.frame);prior=G[(G.file==r.file)&(G.frame<f)&G.adopted_target.notna()];q=d['head'][f].copy();q[2]=40
  if len(prior):j=int(np.flatnonzero(d['mapping']==int(prior.iloc[-1].adopted_target))[0]);q=d['targets'][f,j]
  events.append(dict(id='counter-'+str(f),type='audit',target=None,t=max(0,float(t[f])),position=vec(q),title='Unassigned original counter increment',text='Not automatically treated as another unique target success. See the goal audit; some increments are compatible with repeat scoring. Marker is anchored to the preceding credited ball when available.'))
 initial=[dict(id=int(tid),position=vec(q)) for tid,q in zip(d['mapping'],d['targets'][0])]
 rid=f'{r.participant}-R{r.run_index}';sampleFactor=np.interp(grid,tt,d['factor'][ix]);data=dict(schema='vr-motion-atlas/1',id=rid,participant=r.participant,condition=int(r.condition),repeat=bool(r.is_favourite_run),runIndex=int(r.run_index),limit=float(np.median(d['limit'][ix])),score=float(r.final_score),duration=float(grid[-1]),sampleHz=10,times=grid.tolist(),tracks=tracks,factor=sampleFactor.tolist(),targets=initial,objects=objects,events=events,headAnchor=tracks['head'][0],ratings=ratings.loc[r.participant].to_dict())
 out=clean(data);(OUT/(rid+'.json')).write_text(json.dumps(out,separators=(',',':'),allow_nan=False));manifest.append({k:out[k] for k in ['id','participant','condition','repeat','runIndex','limit','score','duration']})
 print(rid,len(grid),len(events),flush=True)
meta=dict(schema='vr-motion-atlas/1',coordinateSystem='metres; x=Unreal Y/100 (right), y=Unreal Z/100 (up), z=-Unreal X/100 (back). No yaw alignment.',sampling='10Hz overview resampling; invalid/gap samples null; events retain raw-frame positions. Not suitable for high-frequency coordination inference.',runs=manifest,targets=clean(initial),caveats=['Subjective ratings are global participant responses, not condition-specific.','Goal attributions and early-release flags remain provisional.','Target selection counts reflect reconstructed manipulations, not stated preferences.','Density is time occupancy in 10cm voxels; not a probability or tested workspace boundary.'])
(OUT/'manifest.json').write_text(json.dumps(meta,separators=(',',':')))
