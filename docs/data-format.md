# Compatible recordings

A run JSON uses schema `vr-motion-atlas/1` with id, participant, condition (1/2/3), runIndex, repeat, limit, score, duration, sampleHz, times, factor, headAnchor, tracks, targets, objects and events. Tracks contains left, right, vl, vr and head arrays, one [x,y,z] or null per time sample. factor has one number per sample. Positions are metres: [Unreal Y/100, Unreal Z/100, -Unreal X/100]. Null samples break trajectories.

Head orientation uses headDirections.forward/right/up arrays of converted unit vectors. Do not apply raw Unreal quaternion components directly to Three.js. For first-person mode, head position plus forward/up are required at the selected time.

Targets: [{id,position:[x,y,z]}]. Objects: [{target,outcome,points:[[time,x,y,z],...],headTargetCm,...}]. Events: [{id,type,t,position,title,text,target,...}]. Empty arrays are valid. ratings may be {}. Optional predictionCases, forecasts, predictionWeights and channelAudit support additional layers. Do not include subjective data without permission.

A comparison bundle uses schema `vr-motion-atlas-bundle/1` and a runs array. Importing does not save data to a server.
