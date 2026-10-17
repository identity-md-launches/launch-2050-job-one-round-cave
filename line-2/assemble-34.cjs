// One-time media assembly: retain only the generated addition on bare rock.
// No network, environment access, secrets or files outside the workspace.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {decode, encode, thumbnail} = require('../line-1/media/finish-wall.cjs');
if (fs.existsSync('dist/line-2/34.json')) throw Error('record already exists');
const oldBytes = fs.readFileSync('artifacts/line-2/wall.png');
if (crypto.createHash('sha256').update(oldBytes).digest('hex') !==
    'f7c7d40f4b1b1508a45e67fa1bfc5e08261a1adfeed9059f808384f05f7f248e')
  throw Error('expected the round-33 inherited wall');
const generatedBytes = fs.readFileSync('artifacts/line-2/wall-v15.png');
const old = decode(oldBytes), generated = decode(generatedBytes);
const output = {...old, pixels: Buffer.from(old.pixels)};
// Only bare rock above the inherited upper-left sieve is included.
const bounds = {left: 163, top: 105, right: 315, bottom: 253};
const feather = 7;
let changed = 0, outside = 0;
for (let y = bounds.top; y < bounds.bottom; y++) {
  for (let x = bounds.left; x < bounds.right; x++) {
    const edge = Math.min(x - bounds.left, bounds.right - 1 - x,
      y - bounds.top, bounds.bottom - 1 - y);
    const alpha = Math.max(0, Math.min(1, edge / feather));
    const i = (y * old.width + x) * 3;
    for (let c = 0; c < 3; c++) output.pixels[i+c] =
      Math.round(old.pixels[i+c] * (1-alpha) + generated.pixels[i+c] * alpha);
  }
}
for (let y = 0; y < old.height; y++) for (let x = 0; x < old.width; x++) {
  const i = (y * old.width + x) * 3;
  if (!old.pixels.subarray(i,i+3).equals(output.pixels.subarray(i,i+3))) {
    changed++;
    if (x < bounds.left || x >= bounds.right || y < bounds.top || y >= bounds.bottom) outside++;
  }
}
if (!changed || outside) throw Error('preservation check failed');
const png = encode(output), jpg = thumbnail(output);
if (!decode(png).pixels.equals(output.pixels)) throw Error('PNG roundtrip failed');
if (jpg.length > 100000) throw Error('preview too large');
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
fs.writeFileSync('artifacts/line-2/wall-v15.png', png);
fs.writeFileSync('artifacts/line-2/wall.png', png);
fs.writeFileSync('dist/line-2/34.jpg', jpg);
const report = {previous_sha256:hash(oldBytes), sha256:hash(png),
  format:'PNG', width:old.width, height:old.height, png_bytes:png.length,
  preview_format:'JPEG', preview_width:512, preview_height:512, preview_bytes:jpg.length,
  bounds, feather, changed_pixels:changed, outside_mark_changed_pixels:outside,
  png_roundtrip_passed:true};
fs.writeFileSync('line-2/media-check-34.json', JSON.stringify(report,null,2)+'\n');
const record = {name:'The Counted Loop', image:'https://api.imd.fun/artifacts/'+hash(png),
  attributes:[{trait_type:'Cave',value:'Lava'}, {trait_type:'Wall',value:'Line 2'},
    {trait_type:'Number',value:34}, {trait_type:'Left behind',value:'ZipBudget'},
    {trait_type:'Meaning',value:'A knotted cord bounds the stones before they enter the basket.'},
    {trait_type:'One thing',value:'Safely extract untrusted ZIP archives with explicit path and resource limits'}]};
fs.writeFileSync('dist/line-2/34.json', JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
