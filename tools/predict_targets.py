import os
"""Causal retrospective forecasts of next new-target attachment; LOPO tuning.
Only pre-cutoff samples define features/availability. Future attachment IDs are labels.
"""
from pathlib import Path
import numpy as np,pandas as pd,json
from scipy.spatial.transform import Rotation
from scipy.stats import rankdata
BASE=Path(os.environ.get('ATLAS_ANALYSIS_ROOT', 'private-analysis'));CACHE=BASE/'event-work/cache';OUT=Path(__file__).resolve().parents[1]/'dist/data';E=pd.read_csv(BASE/'event-work/results/events.csv');INV=pd.read_csv(BASE/'subjective-work/run_final_scores.csv');HORIZONS=[.25,.5,1.,2.];cases=[];exclusions=[];run_cache={}
def load(r):
 d=dict(np.load(CACHE/r.file.replace('.ndjson','.npz')));q=np.load(CACHE/r.file.replace('.ndjson','_head_rotation.npy'));t=60-d['ts'];active=np.flatnonzero(t>1e-6);i0=max(0,active[0]-1);n=len(t);activation=np.full(43,n,dtype=int)
 for j in range(43):
  resets=np.flatnonzero((d['targets'][:i0,j,2]<20)&(d['targets'][1:i0+1,j,2]>50))+1;start=int(resets[-1]) if len(resets) else 0
  floor=np.flatnonzero(d['targets'][start:,j,2]<20);att=np.flatnonzero((d['attached']==j)&(np.arange(n)>=start));activation[j]=min(int(floor[0]+start) if len(floor) else n,int(att[0]) if len(att) else n)
 d.update(q=q,t=t,i0=i0,activation=activation);return d

def features(d,query):
 t=d['t'];f=int(np.searchsorted(t,query,side='right')-1);p=int(np.searchsorted(t,query-.3,side='right')-1)
 if p<d['i0'] or f<=p:return None,'insufficient_history'
 if d['attached'][f]>=0:return None,'another_target_attached'
 head=d['head'][f];ph=d['head'][p]
 if any(np.linalg.norm(d[k][f]-head)>limit or np.linalg.norm(d[k][p]-ph)>limit for k,limit in [('left',200),('right',200),('vl',600),('vr',600)]):return None,'invalid_tracking'
 ids=np.flatnonzero(d['activation']>f)
 if len(ids)<2:return None,'too_few_candidates'
 qs=d['q'][[p,f]].astype(float);norm=np.linalg.norm(qs,axis=1)
 if not np.isfinite(qs).all() or np.any(norm<.5):return None,'invalid_head_rotation'
 forward=Rotation.from_quat(qs/norm[:,None]).apply([[1,0,0],[1,0,0]])
 target=d['targets'][f,ids];past=d['targets'][p,ids];delta=target-head;pdiff=past-ph
 angle=np.arccos(np.clip(delta@forward[1]/np.maximum(np.linalg.norm(delta,axis=1),1e-9),-1,1))*180/np.pi
 pangle=np.arccos(np.clip(pdiff@forward[0]/np.maximum(np.linalg.norm(pdiff,axis=1),1e-9),-1,1))*180/np.pi
 distance=np.minimum(np.linalg.norm(target-d['vl'][f],axis=1),np.linalg.norm(target-d['vr'][f],axis=1));pdistance=np.minimum(np.linalg.norm(past-d['vl'][p],axis=1),np.linalg.norm(past-d['vr'][p],axis=1));dt=t[f]-t[p]
 closing=(pdistance-distance)/dt;angular=(pangle-angle)/dt
 raw=np.stack([distance,-closing,angle,-angular],axis=1);ranks=np.stack([(rankdata(raw[:,k],method='average')-1)/(len(ids)-1) for k in range(4)],axis=1)
 return dict(frame=f,featureTime=float(t[f]),historyTime=float(t[p]),ids=d['mapping'][ids].astype(int),ranks=ranks,positions=np.stack([target[:,1]/100,target[:,2]/100,-target[:,0]/100],axis=1),headAngles=angle,distance=distance,closing=closing),None

def main():
 for n,r in enumerate(INV.itertuples()):
  d=load(r);rid=f'{r.participant}-R{r.run_index}';run_cache[rid]=(r,d)
  es=E[(E.file==r.file)&E.logged_attachment&E.timed_attachment].sort_values('first_frame')
  starts=es.first_frame.to_numpy(int)
  for e in es.itertuples():
   for horizon in HORIZONS:
    grab=float(d['t'][e.first_frame]);query=grab-horizon;f,reason=features(d,query)
    if f is None:exclusions.append(dict(id=rid,participant=r.participant,repeat=bool(r.is_favourite_run),horizon=horizon,reason=reason));continue
    if np.any((starts<e.first_frame)&(d['t'][starts]>query)):exclusions.append(dict(id=rid,participant=r.participant,repeat=bool(r.is_favourite_run),horizon=horizon,reason='another_new_pickup_before_label'));continue
    truth=np.flatnonzero(f['ids']==e.target)
    if not len(truth):exclusions.append(dict(id=rid,participant=r.participant,repeat=bool(r.is_favourite_run),horizon=horizon,reason='truth_unavailable_at_cutoff'));continue
    cases.append(dict(id=rid,participant=r.participant,condition=int(r.condition),repeat=bool(r.is_favourite_run),runIndex=int(r.run_index),target=int(e.target),grabTime=grab,queryTime=query,horizon=horizon,truth=int(truth[0]),headAngle=float(f['headAngles'][truth[0]]),**f))
  print(n+1,rid,len(es),flush=True)
 # quarter-simplex weights; ties prefer fewer features, then no head-turn term, then distance.
 weights=[]
 for a in range(5):
  for b in range(5-a):
   for c in range(5-a-b):weights.append(np.array([a,b,c,4-a-b-c],dtype=float)/4)
 weights.sort(key=lambda w:(np.count_nonzero(w),w[3]>0,-w[0],-w[1],-w[2]))
 people=list(INV.participant.unique());selected={};results=[];metrics=[]
 for horizon in HORIZONS:
  pool=[c for c in cases if c['horizon']==horizon and not c['repeat']]
  for pid in people:
   train=[c for c in pool if c['participant']!=pid];scores=[]
   for w in weights:
    by={}
    for c in train:by.setdefault(c['participant'],[]).append(int(np.argmin(c['ranks']@w)==c['truth']))
    scores.append(np.mean([np.mean(v) for v in by.values()]))
   w=weights[int(np.argmax(scores))];selected[(pid,horizon)]=w
  for c in [c for c in cases if c['horizon']==horizon]:
   methods={'nearest_hand':np.array([1,0,0,0]),'head_forward':np.array([0,0,1,0]),'hand_approach':np.array([.5,.5,0,0]),'combined_lopo':selected[(c['participant'],horizon)]}
   row={k:c[k] for k in ['id','participant','condition','repeat','runIndex','target','grabTime','queryTime','featureTime','historyTime','horizon','headAngle']};row['candidates']=len(c['ids']);row['cutoff_frame']=c['frame']
   for name,w in methods.items():
    order=np.argsort(c['ranks']@w,kind='stable');top=c['ids'][order[:3]];row[name+'_top1']=int(top[0]);row[name+'_top3']=','.join(map(str,top));row[name+'_hit1']=int(top[0]==c['target']);row[name+'_hit3']=int(c['target'] in top)
   row.update({k:float(v) for k,v in zip(['w_distance','w_hand_closing','w_head_angle','w_head_turn'],selected[(c['participant'],horizon)])});results.append(row)
 R=pd.DataFrame(results);R.to_csv(OUT/'prediction_backtest.csv',index=False);pd.DataFrame(exclusions).to_csv(OUT/'prediction_exclusions.csv',index=False)
 for horizon,v in R[~R['repeat']].groupby('horizon'):
  for method in ['nearest_hand','head_forward','hand_approach','combined_lopo']:
   per=v.groupby('participant')[[method+'_hit1',method+'_hit3']].mean();metrics.append(dict(horizon=horizon,method=method,episodes=len(v),participants=len(per),top1=float(per.iloc[:,0].mean()),top3=float(per.iloc[:,1].mean()),medianHeadAngle=float(v.headAngle.median()),within15deg=float((v.headAngle<=15).mean()),within30deg=float((v.headAngle<=30).mean())))
 M=pd.DataFrame(metrics);M.to_csv(OUT/'prediction_summary.csv',index=False)
 summary=dict(primaryHorizon=.5,features=['virtual-hand distance','virtual-hand closing speed over past 0.3s','head-forward angle','head-angle closing rate over past 0.3s'],training='Leave one participant out; select quarter-step rank-combination weights using mean participant accuracy of other participants’ main runs only. Favourite runs excluded from tuning and primary evaluation.',caveat='Retrospective event-aligned prediction of next new-target attachment, only when no target is attached at the cutoff. This does not validate intention, failed-attempt labels, eye gaze, or continuous false-positive rates.',metrics=metrics)
 (OUT/'prediction_summary.json').write_text(json.dumps(summary,separators=(',',':')))
 # Store fixed-horizon audit cases and causal top-three forecasts at every display time.
 for rid,(r,d) in run_cache.items():
  p=OUT/(rid+'.json');run=json.loads(p.read_text());v=R[(R.id==rid)&(R.horizon==.5)];run['predictionCases']=json.loads(v.to_json(orient='records'));
  for case in run['predictionCases']:
   feat,_=features(d,case['queryTime']);order=[int(np.flatnonzero(feat['ids']==int(target))[0]) for target in case['combined_lopo_top3'].split(',')];case['positions']=np.round(feat['positions'][order],4).tolist()
  run['predictionWeights']=selected[(r.participant,.5)].tolist();forecast=[]
  for query in run['times']:
   f,reason=features(d,query)
   if f is None:forecast.append(None);continue
   score=f['ranks']@selected[(r.participant,.5)];order=np.argsort(score,kind='stable')[:3];forecast.append(dict(targets=f['ids'][order].tolist(),positions=np.round(f['positions'][order],4).tolist(),ranks=[round(float(score[k]),3) for k in order],featureTime=round(f['featureTime'],4),candidateCount=len(f['ids'])))
  run['forecasts']=forecast;run['predictionMethod']='LOPO rank-combination model tuned at 0.5s before new target attachments; scores are ranks, not probabilities. Continuous display is exploratory.';p.write_text(json.dumps(run,separators=(',',':'),allow_nan=False))
 print(M.to_string(index=False))

if __name__=='__main__':main()
