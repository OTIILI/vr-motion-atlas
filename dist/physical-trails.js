import * as THREE from 'three';
import {Line2} from './vendor/lines/Line2.js';
import {LineGeometry} from './vendor/lines/LineGeometry.js';
import {LineMaterial} from './vendor/lines/LineMaterial.js';
// Screen-space width is intentional: the stroke is an analytical marker, not limb diameter.
export function makePhysicalTrail(points,color,{fallback=false,width=3,foreground=true}={}){
 if(points.length<2)return null;
 let line;
 if(fallback){line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p))),new THREE.LineBasicMaterial({color,opacity:1,transparent:true,depthWrite:false,depthTest:!foreground}));}
 else{const geometry=new LineGeometry();geometry.setPositions(points.flat());const material=new LineMaterial({color,linewidth:width,worldUnits:false,opacity:1,transparent:true,depthWrite:false,depthTest:!foreground});line=new Line2(geometry,material);line.computeLineDistances();}
 line.userData.strokeWidth=width;line.userData.layer='physical-trail';line.renderOrder=foreground?30:0;line.frustumCulled=false;return line;
}
