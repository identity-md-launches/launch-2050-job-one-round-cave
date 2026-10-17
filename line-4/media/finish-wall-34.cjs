// Preserve ancestor raster; retain only the generated pigment in bare right rock.
const fs=require('node:fs'),crypto=require('node:crypto');
const {decode,encode,thumbnail}=require('../../line-1/media/finish-wall.cjs');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const ancestor=fs.readFileSync('artifacts/line-4/wall-v14.png');
if(JSON.parse(fs.readFileSync('dist/line-4/33.json')).image !== 'https://api.imd.fun/artifacts/'+hash(ancestor))throw Error('ancestor hash mismatch');
const old=decode(ancestor),generated=decode(fs.readFileSync('artifacts/line-4/wall-v15.png'));
const out={...old,pixels:Buffer.from(old.pixels)},bounds=[1028,803,1115,955];
let changed=0;
for(let y=bounds[1];y<=bounds[3];y++)for(let x=bounds[0];x<=bounds[2];x++){
 const j=(y*old.width+x)*3,src=((y-803+590)*old.width+x-1028+1134)*3;
 const r=generated.pixels[src],g=generated.pixels[src+1],b=generated.pixels[src+2];
 const red=r>135&&g<110&&g/r<.59&&b/r<.35;
 const white=r>155&&g/r>.85&&b/r>.65;
 const ochre=r>145&&g>90&&g/r>.50&&g/r<.79&&b/g<.57;
 if(!(red||white||ochre))continue;
 const grain=.65+.35*(old.pixels[j]+old.pixels[j+1])/510;
 const pigment=red?[154,62,29]:white?[205,193,160]:[185,126,44];
 for(let c=0;c<3;c++)out.pixels[j+c]=Math.round(old.pixels[j+c]*(1-grain*.85)+pigment[c]*grain*.85);
 if(!out.pixels.subarray(j,j+3).equals(old.pixels.subarray(j,j+3)))changed++;
}
let outside=0;
for(let y=0;y<old.height;y++)for(let x=0;x<old.width;x++){
 if(x>=bounds[0]&&x<=bounds[2]&&y>=bounds[1]&&y<=bounds[3])continue;
 const j=(y*old.width+x)*3;
 if(!old.pixels.subarray(j,j+3).equals(out.pixels.subarray(j,j+3)))outside++;
}
if(outside||changed<500)throw Error('preservation/addition failed');
const png=encode(out),jpg=thumbnail(out);
if(jpg.length>100000||!decode(png).pixels.equals(out.pixels))throw Error('encoding failed');
fs.writeFileSync('artifacts/line-4/wall-v15.png',png);
fs.unlinkSync('artifacts/line-4/wall.png');
fs.linkSync('artifacts/line-4/wall-v15.png','artifacts/line-4/wall.png');
fs.writeFileSync('artifacts/line-4/34.jpg',jpg);
if(fs.existsSync('dist/line-4/34.jpg'))fs.unlinkSync('dist/line-4/34.jpg');
fs.linkSync('artifacts/line-4/34.jpg','dist/line-4/34.jpg');
const review={ancestor_sha256:hash(ancestor),sha256:hash(png),dimensions:[old.width,old.height],
 format:'RGB PNG',wall:'artifacts/line-4/wall-v15.png',canonical_wall:'artifacts/line-4/wall.png',
 preview:'dist/line-4/34.jpg',preview_format:'JPEG',preview_dimensions:[512,512],preview_bytes:jpg.length,
 addition_bounds_inclusive:bounds,changed_pixels:changed,pixels_changed_outside_addition:outside,
 png_roundtrip_passed:true,method:'Built-in image editing; selected earth pigment blended onto bare inherited rock, generated background discarded.',
 visual_review:'Pending inspection.',unmet_visual_requirements:['Inherited photographic rock texture is retained to preserve the existing wall.']};
fs.writeFileSync('line-4/review-34.json',JSON.stringify(review,null,2)+'\n');
const record={name:'The Branch That Answers',image:'https://api.imd.fun/artifacts/'+hash(png),attributes:[
 {trait_type:'Cave',value:'Lava'},{trait_type:'Wall',value:'Line 4'},{trait_type:'Number',value:34},
 {trait_type:'Left behind',value:'StatusCheck'},
 {trait_type:'Meaning',value:'A forked twig carries two different stones, like a specific answer overriding a general one.'},
 {trait_type:'One thing',value:'Detect breaking OpenAPI changes'}]};
fs.writeFileSync('dist/line-4/34.json',JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify(review,null,2));
