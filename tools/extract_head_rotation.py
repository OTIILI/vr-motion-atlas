import os
"""Cache raw headset quaternions without changing any recorded hand labels."""
from pathlib import Path
import json,zipfile,numpy as np,pandas as pd
BASE=Path(os.environ.get('ATLAS_ANALYSIS_ROOT', 'private-analysis'));CACHE=BASE/'event-work/cache';inv=pd.read_csv(BASE/'subjective-work/run_final_scores.csv');z=zipfile.ZipFile(BASE/'event-work/Datas.zip')
for k,r in inv.iterrows():
 out=CACHE/r.file.replace('.ndjson','_head_rotation.npy')
 if out.exists():continue
 name='Datas/'+r.participant+'/'+r.file
 rows=[]
 # First 76 files are compact NDJSON; remaining pretty objects need streaming raw_decode.
 with z.open(name) as f:first=f.readline()
 if first.strip()==b'{':
  raw=z.read(name).decode('utf-8-sig');offset=0;decoder=json.JSONDecoder()
  while offset<len(raw):
   while offset<len(raw) and raw[offset].isspace():offset+=1
   if offset>=len(raw):break
   d,offset=decoder.raw_decode(raw,offset);q=d['headTransform']['rotation'];rows.append([q[a] for a in ['x','y','z','w']])
 else:
  for line in z.open(name):
   if not line.strip():continue
   q=json.loads(line)['headTransform']['rotation'];rows.append([q[a] for a in ['x','y','z','w']])
 arr=np.asarray(rows,dtype=np.float32);assert len(arr)==len(np.load(CACHE/r.file.replace('.ndjson','.npz'))['ts']);np.save(out,arr);print(k+1,r.participant,len(arr),flush=True)
