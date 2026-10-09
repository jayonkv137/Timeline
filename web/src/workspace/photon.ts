/** Analytic two-source diffusion through one frosted sphere; a display approximation, not a path tracer. */
const cache=new Map<string,string>();
export function photonTexture(human:number,ai:number){
 const mass=human+ai,ratio=mass?human/mass:.5,key=(Math.round(ratio*100)/100).toString();
 if(cache.has(key))return cache.get(key)!;
 const canvas=document.createElement('canvas');canvas.width=canvas.height=128;
 const ctx=canvas.getContext('2d')!,img=ctx.createImageData(128,128);
 const h=[56/255,189/255,248/255],a=[251/255,146/255,60/255];
 for(let y=0;y<128;y++)for(let x=0;x<128;x++){
  const nx=(x-63.5)/62,ny=(y-63.5)/62,d=nx*nx+ny*ny;if(d>1)continue;
  const z=Math.sqrt(1-d),u=ratio*Math.exp(-((nx+.2)**2+ny*ny)*1.4),v=(1-ratio)*Math.exp(-((nx-.2)**2+ny*ny)*1.4);
  const fusion=2*Math.sqrt(u*v)*Math.exp(-d*1.8),rim=(1-z)**3;
  const spec=Math.exp(-((nx+.26)**2+(ny+.34)**2)*35)*.48;
  const shade=.32+.68*z,idx=(y*128+x)*4;
  for(let c=0;c<3;c++)img.data[idx+c]=255*Math.min(1,Math.pow((h[c]*u+a[c]*v)*1.3*shade+fusion*.82+rim*.24+spec+.018,.86));
  img.data[idx+3]=255*Math.min(1,(1-Math.sqrt(d))*125);
 }
 ctx.putImageData(img,0,0);const url=canvas.toDataURL();cache.set(key,url);return url;
}
