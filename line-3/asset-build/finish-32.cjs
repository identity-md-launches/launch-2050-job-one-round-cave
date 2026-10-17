// Transfer only generated pigment onto bare ancestral rock. No network or configuration.
const fs=require('node:fs'), crypto=require('node:crypto');
const media=require('./png_codec.cjs');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const source='artifacts/line-3/wall-v14.png', destination='artifacts/line-3/wall-v15.png';
const ancestral=fs.readFileSync(source), generatedBytes=fs.readFileSync(destination);
if(hash(ancestral)!=='86f721b579e7c71f9a07b708121ee70d3d78c1e0574877b8c911865ea9968e6a') throw Error('Wrong ancestor');
const old=media.decode(ancestral), generated=media.decode(generatedBytes);
const out={...old,pixels:Buffer.from(old.pixels)}, box=[82,425,125,70];
let changed=0;
for(let dy=0;dy<box[3];dy++) for(let dx=0;dx<box[2];dx++) {
  // Crop motif from tool output. No generated background is copied.
  const gx=Math.floor(95+dx*1080/box[2]), gy=Math.floor(375+dy*540/box[3]);
  const gi=(gy*generated.width+gx)*3, [r,g,b]=generated.pixels.subarray(gi,gi+3);
  const charcoal=r<90 && g<78 && b<65;
  const red=r>95 && r>g*1.6 && g<115 && r-b>65;
  const cord=gy>670 && gy<915 && ((gx>355 && gx<495)||(gx>775 && gx<915));
  const ochre=cord && r>130 && g>85 && g<165 && r-g>45 && g-b>35;
  if(!charcoal && !red && !ochre) continue;
  const color=charcoal?[40,30,23]:red?[151,63,30]:[179,120,47];
  const alpha=charcoal?.70:red?.65:.50;
  const i=((box[1]+dy)*old.width+box[0]+dx)*3;
  for(let c=0;c<3;c++) out.pixels[i+c]=Math.round(old.pixels[i+c]*(1-alpha)+color[c]*alpha);
  changed++;
}
let outside=0;
for(let y=0;y<old.height;y++) for(let x=0;x<old.width;x++) {
  if(x>=box[0] && x<box[0]+box[2] && y>=box[1] && y<box[1]+box[3]) continue;
  const i=(y*old.width+x)*3;
  if(!out.pixels.subarray(i,i+3).equals(old.pixels.subarray(i,i+3))) outside++;
}
if(outside || changed<300) throw Error('Preservation failure');
const bytes=media.encode(out), preview=media.thumbnail(out);
if(!media.decode(bytes).pixels.equals(out.pixels) || preview.length>100000) throw Error('Format check failed');
fs.writeFileSync(destination,bytes);
fs.unlinkSync('artifacts/line-3/wall.png');
fs.symlinkSync('wall-v15.png','artifacts/line-3/wall.png');
fs.writeFileSync('dist/line-3/32.jpg',preview,{flag:'wx'});
const result={source,source_sha256:hash(ancestral),generated_sha256:hash(generatedBytes),output:destination,
  output_sha256:hash(bytes),patch_xywh:box,changed_pixels:changed,changed_pixels_outside_patch:outside,
  png_dimensions:[old.width,old.height],png_format:'RGB PNG',png_bytes:bytes.length,
  jpeg_dimensions:[512,512],jpeg_format:'JPEG',jpeg_bytes:preview.length,
  method:'Only generated tray pigment blended onto original rock. All pixels outside patch preserved.'};
fs.writeFileSync('line-3/asset-build/preservation-32.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result,null,2));
