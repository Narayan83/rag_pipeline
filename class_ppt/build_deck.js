const pptxgen = require('pptxgenjs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE'; // 13.333 x 7.5
pptx.author = 'OpenAI';
pptx.subject = 'Teaching deck: chunking strategies for RAG';
pptx.title = 'Chunking Strategies for RAG';
pptx.company = 'OpenAI';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US'
};
pptx.defineSlideMaster({
  title: 'MASTER',
  background: { color: '07111F' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.08, fill: { color: '22D3EE' }, line: { color: '22D3EE' } } },
    { text: { text: 'CHUNKING STRATEGIES FOR RAG', options: { x: 0.55, y: 7.08, w: 4.2, h: 0.22, fontFace: 'Aptos', fontSize: 8.5, color: '70869B', margin: 0 } } },
  ],
  slideNumber: { x: 12.35, y: 7.02, w: 0.35, h: 0.25, color: '70869B', fontFace: 'Aptos', fontSize: 9, align: 'right' }
});

const C = {
  bg: '07111F', card: '0F1D2E', card2: '13263B', text: 'ECF4FA', muted: '9FB3C8',
  cyan: '22D3EE', purple: 'A78BFA', green: '34D399', orange: 'FB923C', red: 'F87171',
  yellow: 'FBBF24', blue: '60A5FA', line: '274157', code: '09131F', white: 'FFFFFF'
};

function slide() { return pptx.addSlide('MASTER'); }
function addTitle(s, title, subtitle) {
  s.addText(title, { x: 0.62, y: 0.35, w: 11.9, h: 0.45, fontFace: 'Aptos Display', fontSize: 26, bold: true, color: C.text, margin: 0, breakLine: false });
  if (subtitle) s.addText(subtitle, { x: 0.64, y: 0.86, w: 11.4, h: 0.35, fontFace: 'Aptos', fontSize: 11.5, color: C.muted, margin: 0 });
}
function pill(s, x, y, text, color=C.cyan, w=1.35) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.34, rectRadius: 0.08, fill: { color, transparency: 84 }, line: { color, transparency: 30, width: 1 } });
  s.addText(text, { x: x+0.08, y: y+0.055, w: w-0.16, h: 0.2, fontSize: 8.5, bold: true, color, align: 'center', margin: 0 });
}
function card(s, x, y, w, h, fill=C.card, line=C.line) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: line, width: 1 } });
}
function codeBlock(s, x, y, w, h, code, highlightLines=[]) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06, fill: { color: C.code }, line: { color: '20374B', width: 1 } });
  const lines = code.trim().split('\n');
  const top = y + 0.22;
  const lineH = (h - 0.38) / Math.max(lines.length, 1);
  highlightLines.forEach(idx => {
    if (idx >= 1 && idx <= lines.length) {
      s.addShape(pptx.ShapeType.rect, { x: x+0.06, y: top+(idx-1)*lineH-0.01, w: w-0.12, h: lineH+0.01, fill: { color: C.cyan, transparency: 90 }, line: { color: C.cyan, transparency: 100 } });
    }
  });
  s.addText(code.trim(), { x: x+0.18, y: y+0.18, w: w-0.33, h: h-0.28, fontFace: 'Aptos Mono', fontSize: 11.1, color: 'D7E5EF', margin: 0, breakLine: false, valign: 'top', fit: 'shrink' });
}
function teachBox(s, x, y, w, text, color=C.green) {
  s.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.72, rectRadius: 0.06, fill: { color, transparency: 88 }, line: { color, transparency: 45 } });
  s.addText('TEACH THIS', { x: x+0.14, y: y+0.10, w: 1.05, h: 0.18, fontSize: 8, bold: true, color, margin: 0 });
  s.addText(text, { x: x+0.14, y: y+0.30, w: w-0.28, h: 0.30, fontSize: 10.5, color: C.text, margin: 0, fit: 'shrink' });
}
function arrow(s, x1,y1,x2,y2,color=C.cyan,width=2) {
  s.addShape(pptx.ShapeType.line, { x:x1,y:y1,w:x2-x1,h:y2-y1, line: { color, width, beginArrowType:'none', endArrowType:'triangle' } });
}
function label(s, x,y,w,text,color=C.muted,size=10,align='left') {
  s.addText(text,{x,y,w,h:0.28,fontFace:'Aptos',fontSize:size,color,margin:0,align,fit:'shrink'});
}
function snippetName(s, x, y, name) {
  s.addText(name, { x, y, w: 3.0, h: 0.25, fontFace: 'Aptos Mono', fontSize: 9.5, color: C.cyan, margin: 0, bold: true });
}

// 1 — Title
{
  const s = slide();
  s.background = { color: C.bg };
  pill(s, 0.68, 0.72, 'TEACHING DECK', C.cyan, 1.55);
  s.addText('Chunking Strategies\nfor RAG', { x: 0.72, y: 1.35, w: 6.7, h: 1.55, fontFace: 'Aptos Display', fontSize: 37, bold: true, color: C.text, margin: 0, breakLine: false });
  s.addText('From fixed windows → recursive → semantic → hierarchical → agentic', { x: 0.76, y: 3.10, w: 6.4, h: 0.55, fontSize: 16, color: C.muted, margin: 0, fit: 'shrink' });
  s.addText('With runnable Python examples for every method', { x: 0.76, y: 3.85, w: 5.8, h: 0.35, fontSize: 11.5, bold: true, color: C.green, margin: 0 });

  // document -> chunks visual
  card(s, 7.62, 1.15, 4.65, 4.75, '0B1725', '24435A');
  s.addText('ONE DOCUMENT', { x: 8.0, y: 1.48, w: 1.8, h: 0.24, fontSize: 9, bold: true, color: C.muted, margin: 0 });
  s.addShape(pptx.ShapeType.roundRect, { x: 8.0, y: 1.85, w: 3.75, h: 1.25, rectRadius: 0.04, fill: { color: 'F4F8FB' }, line: { color: 'F4F8FB' } });
  for (let i=0;i<5;i++) s.addShape(pptx.ShapeType.rect,{x:8.28,y:2.05+i*0.17,w:2.85-(i%2)*0.55,h:0.055,fill:{color:'7890A2'},line:{color:'7890A2'}});
  arrow(s, 9.88, 3.25, 9.88, 3.77, C.cyan, 2);
  s.addText('different chunking strategies', { x: 8.55, y: 3.34, w: 2.7, h: 0.3, fontSize: 9.5, italic: true, align: 'center', color: C.cyan, margin: 0 });
  const bx=8.05, by=4.0, bw=0.73, gap=0.16;
  [C.cyan,C.purple,C.green,C.orange,C.blue].forEach((col,i)=>{
    s.addShape(pptx.ShapeType.roundRect,{x:bx+i*(bw+gap),y:by+(i%2)*0.12,w:bw,h:1.08-(i%2)*0.12,rectRadius:0.04,fill:{color:col,transparency:12},line:{color:col}});
  });
  s.addText('retrieve the right context', { x: 8.1, y: 5.38, w: 3.6, h: 0.28, fontSize: 11.5, bold: true, color: C.text, align: 'center', margin: 0 });
}

// 2 — Why chunking
{
  const s = slide(); addTitle(s,'Why chunking changes RAG quality','The retriever can only return the units you choose to index.');
  const stages = [
    ['DOCUMENT','long + mixed topics',C.blue],['CHUNK','choose boundaries',C.cyan],['EMBED','vector per chunk',C.purple],['RETRIEVE','top-k matches',C.green],['LLM','answer with context',C.orange]
  ];
  let x=0.75;
  stages.forEach((st,i)=>{
    card(s,x,1.55,2.15,1.25,'0D1B2A',st[2]);
    s.addText(st[0],{x:x+0.15,y:1.82,w:1.85,h:0.25,fontSize:13,bold:true,color:st[2],align:'center',margin:0});
    s.addText(st[1],{x:x+0.14,y:2.18,w:1.88,h:0.22,fontSize:9.5,color:C.muted,align:'center',margin:0});
    if(i<stages.length-1) arrow(s,x+2.2,2.17,x+2.55,2.17,C.line,1.6);
    x+=2.5;
  });
  s.addText('A good chunk balances three forces', { x: 0.8, y: 3.25, w: 4.0, h: 0.3, fontSize: 14, bold: true, color: C.text, margin: 0 });
  const boxes=[
    {x:0.82,title:'PRECISION',txt:'Small chunks retrieve the exact fact.',col:C.cyan},
    {x:4.28,title:'CONTEXT',txt:'Larger chunks preserve surrounding meaning.',col:C.green},
    {x:7.74,title:'COST',txt:'More / larger chunks increase storage & tokens.',col:C.orange}
  ];
  boxes.forEach(b=>{
    card(s,b.x,3.78,3.0,1.35,'0F1D2E',b.col);
    s.addText(b.title,{x:b.x+0.18,y:4.02,w:2.6,h:0.25,fontSize:11,bold:true,color:b.col,margin:0});
    s.addText(b.txt,{x:b.x+0.18,y:4.38,w:2.62,h:0.42,fontSize:11.5,color:C.text,margin:0,fit:'shrink'});
  });
  teachBox(s, 10.87, 3.78, 1.7, 'No method wins everywhere. Pick boundaries that match your document + query.', C.purple);
}

// 3 — Same document
{
  const s = slide(); addTitle(s,'Same document. Different cuts.','We will reuse one Employee Leave Policy throughout the deck.');
  card(s,0.72,1.33,5.95,4.95,'0C1927','23435B');
  s.addText('Employee Leave Policy', { x: 1.05, y: 1.65, w: 4.8, h: 0.33, fontSize: 19, bold: true, color: C.text, margin: 0 });
  s.addText('3. Annual Leave', { x: 1.05, y: 2.14, w: 2.8, h: 0.28, fontSize: 13, bold: true, color: C.cyan, margin: 0 });
  const para='Eligible employees receive 20 days of annual leave per calendar year. Up to 5 unused days may be carried into the next year. Carried-over leave must be used by March 31 or it expires.';
  s.addText(para,{x:1.05,y:2.55,w:5.0,h:1.16,fontSize:14,color:C.text,margin:0.02,breakLine:false,fit:'shrink'});
  s.addText('Managers should consider business coverage before approving leave. Requests longer than 5 consecutive working days should normally be submitted at least 30 days in advance.',{x:1.05,y:4.05,w:5.0,h:1.0,fontSize:12.5,color:C.muted,margin:0.02,fit:'shrink'});
  s.addText('Question: “How many days can I carry forward?”',{x:1.05,y:5.45,w:4.9,h:0.34,fontSize:13.5,bold:true,color:C.green,margin:0});

  s.addText('Possible boundaries', { x: 7.18, y: 1.52, w: 3.0, h: 0.28, fontSize: 13, bold: true, color: C.text, margin: 0 });
  const rows=[
    ['Fixed','every N tokens',C.blue],['Recursive','natural separator + size',C.cyan],['Semantic','meaning shift',C.purple],['Hierarchical','section / parent path',C.green],['Agentic','LLM decides boundary',C.orange]
  ];
  rows.forEach((r,i)=>{
    const yy=2.0+i*0.78;
    card(s,7.15,yy,5.15,0.58,'0F1D2E',r[2]);
    s.addText(r[0],{x:7.38,y:yy+0.14,w:1.25,h:0.22,fontSize:10.5,bold:true,color:r[2],margin:0});
    s.addText(r[1],{x:8.72,y:yy+0.14,w:3.2,h:0.22,fontSize:10.5,color:C.text,margin:0});
  });
  teachBox(s, 7.15, 6.08, 5.15, 'The document is constant. Only the rule for drawing boundaries changes.', C.cyan);
}

// 4 Fixed
{
  const s = slide(); addTitle(s,'1 · Fixed-size chunking','Baseline: split every N units — simple, fast, predictable.');
  pill(s,0.75,1.25,'BOUNDARY = SIZE',C.blue,1.7);
  const x0=0.82,y0=1.95,w=5.5;
  s.addText('Document stream', { x:x0,y:y0-0.35,w:2,h:0.25,fontSize:10.5,color:C.muted,margin:0 });
  for(let i=0;i<4;i++){
    s.addShape(pptx.ShapeType.roundRect,{x:x0+i*1.28,y:y0,w:1.08,h:0.82,rectRadius:0.04,fill:{color:[C.blue,C.cyan,C.purple,C.green][i],transparency:18},line:{color:[C.blue,C.cyan,C.purple,C.green][i]}});
    s.addText(`${i*55+1}–${(i+1)*55}`,{x:x0+i*1.28+0.08,y:y0+0.26,w:0.92,h:0.2,fontSize:9,bold:true,color:C.text,align:'center',margin:0});
  }
  arrow(s,1.9,3.05,1.9,3.7,C.red,2);
  s.addText('can cut through a sentence / concept',{x:0.9,y:3.82,w:3.4,h:0.3,fontSize:11.5,color:C.red,margin:0});
  card(s,0.82,4.45,5.25,1.05,'0F1D2E',C.line);
  s.addText('Good for', { x:1.05,y:4.68,w:0.8,h:0.22,fontSize:10,bold:true,color:C.green,margin:0 });
  s.addText('fast baselines · uniform text · benchmarking',{x:1.86,y:4.68,w:3.75,h:0.22,fontSize:10.5,color:C.text,margin:0});
  s.addText('Risk', { x:1.05,y:5.04,w:0.8,h:0.22,fontSize:10,bold:true,color:C.orange,margin:0 });
  s.addText('boundary facts lose their neighbors',{x:1.86,y:5.04,w:3.75,h:0.22,fontSize:10.5,color:C.text,margin:0});
  snippetName(s,6.72,1.36,'fixed_size_chunking.py');
  codeBlock(s,6.68,1.68,5.85,3.75,`
def fixed_size_chunks(text, chunk_size=60):
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

chunks = fixed_size_chunks(text, 55)`,[2,4]);
  teachBox(s,6.68,5.72,5.85,'In this teaching code, “words” stand in for model tokens. Production systems should count with the model tokenizer.',C.blue);
}

// 5 overlap
{
  const s = slide(); addTitle(s,'2 · Sliding window + overlap','Repeat some text across adjacent chunks so boundary facts appear in both.');
  pill(s,0.75,1.25,'BOUNDARY = SIZE + STRIDE',C.cyan,2.2);
  const yy=2.05;
  s.addShape(pptx.ShapeType.roundRect,{x:0.95,y:yy,w:4.55,h:0.68,rectRadius:0.04,fill:{color:C.blue,transparency:12},line:{color:C.blue}});
  s.addShape(pptx.ShapeType.roundRect,{x:2.28,y:yy+0.92,w:4.55,h:0.68,rectRadius:0.04,fill:{color:C.cyan,transparency:12},line:{color:C.cyan}});
  s.addShape(pptx.ShapeType.roundRect,{x:3.61,y:yy+1.84,w:4.55,h:0.68,rectRadius:0.04,fill:{color:C.purple,transparency:12},line:{color:C.purple}});
  s.addText('chunk 1',{x:1.1,y:yy+0.21,w:0.8,h:0.2,fontSize:9.5,bold:true,color:C.text,margin:0});
  s.addText('chunk 2',{x:2.43,y:yy+1.13,w:0.8,h:0.2,fontSize:9.5,bold:true,color:C.text,margin:0});
  s.addText('chunk 3',{x:3.76,y:yy+2.05,w:0.8,h:0.2,fontSize:9.5,bold:true,color:C.text,margin:0});
  s.addShape(pptx.ShapeType.rect,{x:2.28,y:yy,w:3.22,h:0.68,fill:{color:C.green,transparency:78},line:{color:C.green,transparency:100}});
  s.addText('overlap',{x:3.36,y:yy+0.22,w:0.9,h:0.2,fontSize:9,bold:true,color:C.green,margin:0,align:'center'});
  teachBox(s,0.92,5.35,5.4,'Overlap improves continuity, but creates more vectors and can return near-duplicate chunks.',C.cyan);
  snippetName(s,7.02,1.36,'sliding_window_chunking.py');
  codeBlock(s,6.88,1.68,5.62,3.9,`
def sliding_window_chunks(text, size=60, overlap=12):
    words = text.split()
    step = size - overlap
    chunks = []

    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
    return chunks`,[3,6]);
  s.addText('Tune overlap as a percentage of chunk size — not as a magic constant.',{x:6.95,y:5.85,w:5.2,h:0.38,fontSize:12.5,bold:true,color:C.orange,margin:0,fit:'shrink'});
}

// 6 paragraph
{
  const s = slide(); addTitle(s,'3 · Sentence / paragraph chunking','Use boundaries already present in natural language.');
  pill(s,0.75,1.25,'BOUNDARY = PUNCTUATION / PARAGRAPH',C.green,2.85);
  card(s,0.82,1.75,5.42,4.75,'0C1927','23435B');
  const paras=[
    ['Eligibility','Employees become eligible after 30 days…',C.cyan],
    ['Annual leave','Employees receive 20 days… carry 5 days…',C.green],
    ['Approval','Requests longer than 5 days… 30 days in advance.',C.orange]
  ];
  paras.forEach((p,i)=>{
    const yy=2.18+i*1.15;
    s.addShape(pptx.ShapeType.roundRect,{x:1.1,y:yy,w:4.78,h:0.82,rectRadius:0.05,fill:{color:p[2],transparency:88},line:{color:p[2],width:1.2}});
    s.addText(p[0],{x:1.3,y:yy+0.13,w:1.2,h:0.22,fontSize:10,bold:true,color:p[2],margin:0});
    s.addText(p[1],{x:2.38,y:yy+0.13,w:3.17,h:0.42,fontSize:10.5,color:C.text,margin:0,fit:'shrink'});
  });
  s.addText('Oversized paragraph?',{x:1.12,y:5.65,w:1.45,h:0.22,fontSize:10,bold:true,color:C.muted,margin:0});
  s.addText('split by sentence → pack again',{x:2.7,y:5.65,w:2.8,h:0.22,fontSize:10.5,color:C.text,margin:0});
  snippetName(s,6.7,1.36,'sentence_paragraph_chunking.py');
  codeBlock(s,6.65,1.68,5.86,4.1,`
paragraphs = re.split(r"\\n\\s*\\n", text)
for paragraph in paragraphs:
    if words(paragraph) <= max_words:
        add(paragraph)
    else:
        for sentence in split_sentences(paragraph):
            pack_without_exceeding(sentence, max_words)`,[1,4,7]);
  teachBox(s,6.65,6.02,5.86,'Great default when prose already has meaningful paragraph structure.',C.green);
}

// 7 recursive
{
  const s = slide(); addTitle(s,'4 · Recursive chunking','Try coarse separators first; fall back only when a piece is still too large.');
  pill(s,0.75,1.25,'BOUNDARY = STRUCTURE + SIZE LIMIT',C.cyan,2.85);
  // cascade diagram
  const stages=[['\\n\\n','sections / paragraphs',C.cyan],['\\n','lines',C.blue],['. ','sentences',C.purple],[' ','words',C.green],['hard split','last resort',C.orange]];
  stages.forEach((st,i)=>{
    const xx=0.92+i*1.08, yy=1.95+i*0.67;
    card(s,xx,yy,2.3,0.72,'0F1D2E',st[2]);
    s.addText(st[0],{x:xx+0.13,y:yy+0.12,w:0.78,h:0.2,fontFace:'Aptos Mono',fontSize:10.5,bold:true,color:st[2],margin:0});
    s.addText(st[1],{x:xx+0.88,y:yy+0.12,w:1.23,h:0.32,fontSize:9.5,color:C.text,margin:0,fit:'shrink'});
    if(i<stages.length-1) arrow(s,xx+2.0,yy+0.66,xx+2.33,yy+0.95,C.line,1.5);
  });
  s.addText('Stop as soon as every chunk fits.',{x:1.0,y:5.65,w:4.0,h:0.3,fontSize:13,bold:true,color:C.green,margin:0});
  snippetName(s,7.15,1.36,'recursive_chunking.py');
  codeBlock(s,6.72,1.68,5.8,4.35,`
SEPARATORS = ["\\n\\n", "\\n", ". ", " ", ""]

def split_piece(piece, level=0):
    if len(piece) <= max_chars:
        return [piece]

    sep = SEPARATORS[level]
    parts = piece.split(sep)
    return recurse_and_merge(parts, level + 1)`,[1,4,7]);
  teachBox(s,6.72,6.2,5.8,'Why it works: it preserves the strongest available boundary without giving up a hard size cap.',C.cyan);
}

// 8 semantic
{
  const s = slide(); addTitle(s,'5 · Semantic chunking','Create a boundary when adjacent ideas stop being similar.');
  pill(s,0.75,1.25,'BOUNDARY = MEANING SHIFT',C.purple,2.1);
  // embedding dots and similarity line
  card(s,0.82,1.72,5.7,4.9,'0C1927','23435B');
  const dots=[
    [1.35,2.35,C.cyan,'S1'],[2.05,2.15,C.cyan,'S2'],[2.72,2.48,C.cyan,'S3'],
    [4.35,3.35,C.purple,'S4'],[4.95,3.02,C.purple,'S5'],[5.45,3.55,C.purple,'S6']
  ];
  dots.forEach(d=>{s.addShape(pptx.ShapeType.ellipse,{x:d[0],y:d[1],w:0.22,h:0.22,fill:{color:d[2]},line:{color:d[2]}});s.addText(d[3],{x:d[0]-0.02,y:d[1]+0.25,w:0.3,h:0.18,fontSize:8,color:C.muted,margin:0,align:'center'});});
  s.addText('topic A',{x:1.45,y:1.95,w:1.2,h:0.2,fontSize:9.5,bold:true,color:C.cyan,margin:0});
  s.addText('topic B',{x:4.55,y:2.68,w:1.2,h:0.2,fontSize:9.5,bold:true,color:C.purple,margin:0});
  s.addShape(pptx.ShapeType.line,{x:3.55,y:1.95,w:0,h:2.15,line:{color:C.red,width:1.8,dash:'dash'}});
  s.addText('similarity drop → boundary',{x:2.78,y:4.2,w:2.1,h:0.25,fontSize:10.5,bold:true,color:C.red,align:'center',margin:0});
  s.addText('cosine similarity between adjacent sentence embeddings',{x:1.16,y:5.25,w:4.9,h:0.4,fontSize:11,color:C.text,margin:0,align:'center'});
  snippetName(s,6.82,1.36,'semantic_chunking.py');
  codeBlock(s,6.68,1.68,5.85,4.35,`
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)
emb = model.encode(sentences, normalize_embeddings=True)

for i in range(1, len(sentences)):
    similarity = float(np.dot(emb[i-1], emb[i]))
    if similarity < threshold:
        start_new_chunk()`,[4,7,8]);
  s.addText('More coherent chunks — but extra embedding work and a threshold to tune.',{x:0.98,y:6.17,w:5.25,h:0.38,fontSize:12,bold:true,color:C.orange,margin:0,fit:'shrink'});
  s.addText('Sentence Transformers docs: encode + similarity / cosine are the core primitives.',{x:6.83,y:6.22,w:5.45,h:0.28,fontSize:9.5,color:C.muted,margin:0,fit:'shrink'});
}

// 9 hierarchical
{
  const s = slide(); addTitle(s,'6 · Hierarchical chunking','Keep the document tree: document → section → paragraph → leaf.');
  pill(s,0.75,1.25,'BOUNDARY = DOCUMENT HIERARCHY',C.green,2.55);
  // tree
  const nodes=[
    {x:2.2,y:1.8,w:2.5,t:'Employee Leave Policy',c:C.green},
    {x:0.82,y:3.0,w:2.3,t:'Annual Leave',c:C.cyan},
    {x:3.55,y:3.0,w:2.3,t:'Sick Leave',c:C.purple},
    {x:0.72,y:4.35,w:1.6,t:'Carry-over',c:C.blue},
    {x:2.43,y:4.35,w:1.6,t:'Approval',c:C.orange},
    {x:3.45,y:4.35,w:1.6,t:'Eligibility',c:C.cyan},
    {x:5.15,y:4.35,w:1.6,t:'Certificate',c:C.purple}
  ];
  nodes.forEach(n=>{card(s,n.x,n.y,n.w,0.62,'0F1D2E',n.c);s.addText(n.t,{x:n.x+0.1,y:n.y+0.19,w:n.w-0.2,h:0.2,fontSize:9.6,bold:true,color:n.c,align:'center',margin:0,fit:'shrink'});});
  [[3.45,2.42,1.98,3.0],[3.45,2.42,4.7,3.0],[1.98,3.62,1.5,4.35],[1.98,3.62,3.23,4.35],[4.7,3.62,4.25,4.35],[4.7,3.62,5.95,4.35]].forEach(a=>arrow(s,...a,C.line,1.2));
  s.addText('Index leaves; retain the path as metadata.',{x:1.0,y:5.55,w:5.2,h:0.3,fontSize:12.5,bold:true,color:C.text,align:'center',margin:0});
  snippetName(s,7.08,1.36,'hierarchical_chunking.py');
  codeBlock(s,6.78,1.68,5.7,4.35,`
@dataclass
class Node:
    title: str
    level: int
    text: str = ""
    children: list["Node"] = field(default_factory=list)

root = parse_markdown_hierarchy(text)
for path, node in root.walk():
    index(text=node.text, metadata={"path": path})`,[2,6,10]);
  teachBox(s,6.78,6.18,5.7,'Useful for manuals, policies, books and documentation where headings carry meaning.',C.green);
}

// 10 parent-child
{
  const s = slide(); addTitle(s,'7 · Parent–child chunking','Retrieve a small child; return its larger parent as generation context.');
  pill(s,0.75,1.25,'PRECISION + CONTEXT',C.orange,1.95);
  card(s,0.82,1.75,5.65,4.8,'0C1927','23435B');
  card(s,1.17,2.05,4.93,1.12,'0F1D2E',C.orange);
  s.addText('PARENT  ·  Annual Leave section',{x:1.42,y:2.28,w:4.35,h:0.26,fontSize:12,bold:true,color:C.orange,margin:0,align:'center'});
  const cx=[1.12,2.72,4.32];
  cx.forEach((xx,i)=>{
    card(s,xx,3.72,1.45,0.92,'0F1D2E',[C.cyan,C.green,C.purple][i]);
    s.addText(`child ${i+1}`,{x:xx+0.12,y:3.93,w:1.2,h:0.2,fontSize:10,bold:true,color:[C.cyan,C.green,C.purple][i],margin:0,align:'center'});
    arrow(s,xx+0.72,3.72,3.63,3.18,C.line,1.2);
  });
  s.addText('Vector index',{x:1.02,y:5.17,w:1.2,h:0.22,fontSize:10,bold:true,color:C.cyan,margin:0});
  s.addText('small children',{x:2.1,y:5.17,w:1.2,h:0.22,fontSize:10,color:C.text,margin:0});
  s.addText('LLM context',{x:3.58,y:5.17,w:1.2,h:0.22,fontSize:10,bold:true,color:C.orange,margin:0});
  s.addText('expanded parent',{x:4.65,y:5.17,w:1.3,h:0.22,fontSize:10,color:C.text,margin:0});
  snippetName(s,6.92,1.36,'parent_child_chunking.py');
  codeBlock(s,6.72,1.68,5.78,4.38,`
parents, children = build_parent_child_chunks(text)

# 1) embed only the small children
index.add([
    {"id": c.child_id, "text": c.text,
     "parent_id": c.parent_id}
    for c in children
])

# 2) after retrieval, expand the hit
context = expand_hit(hit, parents)`,[3,10,11]);
  teachBox(s,6.72,6.2,5.78,'A common pattern when retrieval precision needs smaller text than the LLM should ultimately read.',C.orange);
}

// 11 structure-aware
{
  const s = slide(); addTitle(s,'8 · Structure-aware chunking','Respect Markdown, tables, code blocks and other document-native units.');
  pill(s,0.75,1.25,'BOUNDARY = FORMAT / SYNTAX',C.blue,2.25);
  const blocks=[
    {y:1.85,h:0.55,t:'# Heading',c:C.cyan},
    {y:2.55,h:0.95,t:'Paragraph\nNatural prose block',c:C.green},
    {y:3.72,h:0.85,t:'| Table | Row |\n| ...   | ... |',c:C.orange},
    {y:4.79,h:1.02,t:'```python\ndef approve(): ...\n```',c:C.purple}
  ];
  blocks.forEach(b=>{card(s,0.98,b.y,4.95,b.h,'0F1D2E',b.c);s.addText(b.t,{x:1.23,y:b.y+0.15,w:4.4,h:b.h-0.2,fontFace:b.c===C.purple?'Aptos Mono':'Aptos',fontSize:10.5,bold:b.h<0.7,color:b.c,margin:0,fit:'shrink'});});
  s.addText('Pack whole blocks until size limit is reached.',{x:1.0,y:6.02,w:4.9,h:0.3,fontSize:12.5,bold:true,color:C.text,align:'center',margin:0});
  snippetName(s,6.88,1.36,'structure_aware_chunking.py');
  codeBlock(s,6.68,1.68,5.84,4.45,`
blocks = markdown_blocks(text)

for block in blocks:
    if block.kind in {"heading", "code", "table"}:
        preserve(block)
    else:
        pack(block)

chunks = pack_blocks(blocks, max_chars=500)`,[1,4,9]);
  teachBox(s,6.68,6.26,5.84,'When the format already encodes meaning, use it instead of throwing it away.',C.blue);
}

// 12 agentic
{
  const s = slide(); addTitle(s,'9 · Agentic / LLM-assisted chunking','Ask a reasoning model whether neighboring segments belong together.');
  pill(s,0.75,1.25,'BOUNDARY = MODEL JUDGMENT',C.orange,2.4);
  card(s,0.82,1.72,5.72,4.9,'0C1927','23435B');
  const items=[['A','Annual leave is 20 days…',C.cyan],['B','Up to 5 unused days carry forward…',C.green],['C','Sick leave covers illness…',C.purple]];
  items.forEach((it,i)=>{
    const yy=2.05+i*1.22;
    card(s,1.05,yy,4.55,0.72,'0F1D2E',it[2]);
    s.addText(it[0],{x:1.18,y:yy+0.20,w:0.35,h:0.2,fontSize:10,bold:true,color:it[2],margin:0});
    s.addText(it[1],{x:1.65,y:yy+0.17,w:3.65,h:0.28,fontSize:10.2,color:C.text,margin:0,fit:'shrink'});
    if(i<2){
      const ans=i===0?'SAME_CHUNK':'NEW_CHUNK'; const col=i===0?C.green:C.red;
      s.addText(ans,{x:2.18,y:yy+0.79,w:2.1,h:0.22,fontSize:9.5,bold:true,color:col,align:'center',margin:0});
      arrow(s,3.28,yy+0.67,3.28,yy+0.79,col,1.4);
    }
  });
  s.addText('Adaptive, but adds latency, cost and model variability.',{x:1.0,y:5.95,w:5.3,h:0.3,fontSize:11.5,bold:true,color:C.orange,align:'center',margin:0});
  snippetName(s,6.9,1.36,'agentic_chunking.py');
  codeBlock(s,6.7,1.68,5.82,4.4,`
def agentic_chunks(text, decide_boundary):
    segments = candidate_segments(text)
    chunks = [[segments[0]]]

    for segment in segments[1:]:
        previous = chunks[-1][-1]
        if decide_boundary(previous, segment):
            chunks.append([segment])
        else:
            chunks[-1].append(segment)
    return chunks`,[1,6,8]);
  teachBox(s,6.7,6.2,5.82,'The supplied file is provider-agnostic: inject your own LLM boundary-decider; the demo fallback is deterministic.',C.orange);
}

// 13 proposition
{
  const s = slide(); addTitle(s,'10 · Proposition-based chunking','Turn text into small atomic claims that can be retrieved independently.');
  pill(s,0.75,1.25,'UNIT = ATOMIC CLAIM',C.green,1.85);
  card(s,0.82,1.72,5.78,4.9,'0C1927','23435B');
  s.addText('Original sentence',{x:1.08,y:2.02,w:1.55,h:0.24,fontSize:10,bold:true,color:C.muted,margin:0});
  card(s,1.05,2.37,5.05,0.92,'0F1D2E',C.line);
  s.addText('Employees receive 20 days of annual leave and may carry 5 unused days into the next year.',{x:1.3,y:2.58,w:4.55,h:0.43,fontSize:11.5,color:C.text,margin:0,fit:'shrink'});
  arrow(s,3.6,3.35,3.6,3.78,C.green,2);
  const props=[['P1','Employees receive 20 days of annual leave.',C.cyan],['P2','Employees may carry 5 unused days into the next year.',C.green]];
  props.forEach((p,i)=>{card(s,1.05,3.95+i*0.93,5.05,0.7,'0F1D2E',p[2]);s.addText(p[0],{x:1.24,y:4.16+i*0.93,w:0.45,h:0.2,fontSize:9.5,bold:true,color:p[2],margin:0});s.addText(p[1],{x:1.82,y:4.12+i*0.93,w:4.0,h:0.28,fontSize:10.5,color:C.text,margin:0,fit:'shrink'});});
  snippetName(s,6.9,1.36,'proposition_chunking.py');
  codeBlock(s,6.7,1.68,5.82,4.35,`
def proposition_chunks(text, decompose):
    propositions = []
    for sentence in sentences(text):
        pieces = decompose(sentence)
        propositions.extend(pieces or [sentence])
    return propositions

# High-quality decompose is usually an NLP / LLM step.`,[1,4,8]);
  teachBox(s,6.7,6.18,5.82,'Very precise retrieval for fact-heavy text; beware losing context or creating ambiguous micro-claims.',C.green);
}

// 14 late chunking
{
  const s = slide(); addTitle(s,'11 · Late chunking / contextual pooling','Encode context first; pool chunk vectors afterwards.');
  pill(s,0.75,1.25,'EMBED FIRST → POOL LATER',C.purple,2.3);
  // pipeline
  const py=2.05;
  card(s,0.88,py,1.65,1.05,'0F1D2E',C.blue); label(s,1.03,py+0.22,1.35,'Whole document',C.blue,11,'center');
  arrow(s,2.58,py+0.52,3.18,py+0.52,C.line,1.8);
  card(s,3.22,py,2.0,1.05,'0F1D2E',C.purple); label(s,3.4,py+0.18,1.64,'Contextual token\nembeddings',C.purple,10.5,'center');
  arrow(s,5.28,py+0.52,5.88,py+0.52,C.line,1.8);
  card(s,5.92,py,1.9,1.05,'0F1D2E',C.green); label(s,6.1,py+0.18,1.55,'Pool by\nchunk spans',C.green,10.5,'center');
  s.addText('Each chunk vector “remembers” surrounding document context.',{x:1.0,y:3.55,w:6.65,h:0.38,fontSize:13,bold:true,color:C.text,align:'center',margin:0,fit:'shrink'});
  s.addText('Caveat: model context window still limits how much text can be contextualized at once.',{x:1.0,y:4.18,w:6.65,h:0.38,fontSize:10.8,color:C.orange,align:'center',margin:0,fit:'shrink'});
  snippetName(s,8.0,1.36,'late_chunking_demo.py');
  codeBlock(s,7.82,1.68,4.72,4.65,`
batch = tokenizer(
    text,
    return_offsets_mapping=True,
    return_tensors="pt"
)

token_vectors = model(**batch).last_hidden_state[0]

for span in chunk_spans:
    mask = tokens_overlapping(span)
    chunk_vector = token_vectors[mask].mean(dim=0)`,[1,7,11]);
  teachBox(s,0.98,5.3,6.75,'This is an educational implementation of the idea: contextualize at document level, then aggregate into chunk-level vectors.',C.purple);
}

// 15 comparison
{
  const s = slide(); addTitle(s,'Compare the methods','Choose by boundary signal, retrieval need and operational cost.');
  const cols=[0.72,2.35,5.02,7.58,10.08,12.02];
  const headers=['Method','Boundary signal','Best trait','Main trade-off','Typical fit'];
  const widths=[1.55,2.55,2.45,2.38,2.5];
  let xx=0.72;
  headers.forEach((h,i)=>{s.addShape(pptx.ShapeType.rect,{x:xx,y:1.4,w:widths[i],h:0.5,fill:{color:'17304A'},line:{color:'274157'}});s.addText(h,{x:xx+0.1,y:1.56,w:widths[i]-0.2,h:0.18,fontSize:9.5,bold:true,color:C.text,margin:0,align:i===0?'left':'center'});xx+=widths[i];});
  const rows=[
    ['Fixed','size','speed','cuts meaning','baseline'],
    ['Overlap','size + stride','continuity','duplication','local context'],
    ['Paragraph','natural language','readability','uneven size','prose'],
    ['Recursive','structure + size','strong default','rule-dependent','general RAG'],
    ['Semantic','embedding similarity','coherence','compute + threshold','topic shifts'],
    ['Hierarchical','document tree','multi-level context','more metadata','manuals / docs'],
    ['Parent-child','small + large units','precision + context','more plumbing','long sections'],
    ['Structure-aware','format / syntax','preserves semantics','parser-specific','code / MD / tables'],
    ['Agentic','LLM judgment','adaptive','latency + variability','messy documents'],
    ['Proposition','atomic claims','fact precision','context loss','fact-heavy corpora'],
    ['Late','contextual tokens','contextual vectors','model complexity','advanced retrieval']
  ];
  const rowH=0.43; const colors=[C.blue,C.cyan,C.green,C.cyan,C.purple,C.green,C.orange,C.blue,C.orange,C.green,C.purple];
  rows.forEach((r,ri)=>{
    let x=0.72; const y=1.9+ri*rowH;
    r.forEach((cell,ci)=>{s.addShape(pptx.ShapeType.rect,{x,y,w:widths[ci],h:rowH,fill:{color:ri%2===0?'0B1724':'0E1C2B'},line:{color:'1C3347',width:0.6}});s.addText(cell,{x:x+0.09,y:y+0.11,w:widths[ci]-0.18,h:0.18,fontSize:8.6,bold:ci===0,color:ci===0?colors[ri]:C.text,margin:0,align:ci===0?'left':'center',fit:'shrink'});x+=widths[ci];});
  });
  s.addText('No “best” chunker exists in isolation — evaluate retrieval on your own queries.',{x:0.95,y:6.78,w:11.8,h:0.3,fontSize:13,bold:true,color:C.cyan,align:'center',margin:0});
}

// 16 decision tree
{
  const s = slide(); addTitle(s,'A practical decision tree','Start with the document’s strongest signal, then add complexity only when needed.');
  const centerX=6.55;
  card(s,5.15,1.34,2.9,0.66,'0F1D2E',C.cyan); label(s,5.35,1.56,2.5,'Does the document have strong structure?',C.text,10.5,'center');
  arrow(s,5.45,2.0,3.25,2.75,C.line,1.5); arrow(s,7.75,2.0,9.85,2.75,C.line,1.5);
  label(s,3.85,2.18,0.5,'YES',C.green,9,'center'); label(s,8.82,2.18,0.5,'NO',C.orange,9,'center');
  card(s,1.72,2.74,3.15,0.72,'0F1D2E',C.green); label(s,1.95,2.97,2.7,'Use structure-aware / hierarchical',C.green,10.3,'center');
  card(s,8.48,2.74,3.15,0.72,'0F1D2E',C.orange); label(s,8.73,2.97,2.65,'Do topics shift inside long prose?',C.text,10.2,'center');
  arrow(s,9.05,3.47,7.4,4.22,C.line,1.5); arrow(s,11.08,3.47,11.1,4.22,C.line,1.5);
  label(s,7.92,3.65,0.5,'YES',C.purple,9,'center'); label(s,11.15,3.65,0.5,'NO',C.cyan,9,'center');
  card(s,5.75,4.18,3.05,0.72,'0F1D2E',C.purple); label(s,5.98,4.42,2.6,'Try semantic chunking',C.purple,10.5,'center');
  card(s,9.65,4.18,2.95,0.72,'0F1D2E',C.cyan); label(s,9.88,4.42,2.5,'Start with recursive',C.cyan,10.5,'center');
  card(s,1.15,4.28,3.75,1.55,'0C1927','23435B');
  s.addText('Need tiny retrieval units but bigger LLM context?',{x:1.48,y:4.62,w:3.08,h:0.46,fontSize:11.5,bold:true,color:C.text,align:'center',margin:0,fit:'shrink'});
  s.addText('→ add parent–child',{x:1.55,y:5.22,w:2.95,h:0.24,fontSize:11,bold:true,color:C.orange,align:'center',margin:0});
  card(s,5.5,5.3,6.75,0.9,'0F1D2E',C.line);
  s.addText('Escalate to agentic / proposition / late chunking only when evaluation shows the simpler strategy is missing your retrieval goals.',{x:5.78,y:5.56,w:6.2,h:0.42,fontSize:11,color:C.text,align:'center',margin:0,fit:'shrink'});
}

// 17 experiment
{
  const s = slide(); addTitle(s,'Hands-on experiment: same query, four chunkers','Measure retrieval quality instead of guessing.');
  card(s,0.78,1.35,12.0,0.78,'0F1D2E',C.green);
  s.addText('QUERY  →  “How many unused annual-leave days can an employee carry into next year?”',{x:1.08,y:1.62,w:11.4,h:0.28,fontSize:13,bold:true,color:C.green,align:'center',margin:0,fit:'shrink'});
  const cards=[
    {x:0.8,t:'Fixed',c:C.blue,a:'May retrieve only half of the sentence if a boundary lands badly.'},
    {x:3.85,t:'Recursive',c:C.cyan,a:'Often keeps the full policy paragraph together.'},
    {x:6.9,t:'Semantic',c:C.purple,a:'Groups the carry-over sentence with nearby annual-leave meaning.'},
    {x:9.95,t:'Parent–child',c:C.orange,a:'Child matches “5 unused days”; parent restores the full section.'}
  ];
  cards.forEach((q,i)=>{
    card(s,q.x,2.55,2.55,2.85,'0C1927',q.c);
    s.addText(q.t,{x:q.x+0.2,y:2.82,w:2.15,h:0.28,fontSize:15,bold:true,color:q.c,align:'center',margin:0});
    s.addText(q.a,{x:q.x+0.24,y:3.42,w:2.08,h:1.18,fontSize:11,color:C.text,align:'center',margin:0.02,fit:'shrink',valign:'mid'});
    s.addText(['boundary risk','strong baseline','topic-aware','precision + context'][i],{x:q.x+0.25,y:4.86,w:2.05,h:0.2,fontSize:9,bold:true,color:C.muted,align:'center',margin:0});
  });
  s.addText('Evaluate: hit rate / recall@k · answer accuracy · duplication · latency · cost',{x:0.95,y:5.9,w:11.5,h:0.35,fontSize:13,bold:true,color:C.text,align:'center',margin:0});
  s.addText('The answer in our sample policy is “up to 5 unused days.” The point of the exercise is whether the retriever reliably surfaces that evidence.',{x:1.25,y:6.42,w:10.9,h:0.42,fontSize:10.5,color:C.muted,align:'center',margin:0,fit:'shrink'});
}

// 18 pack
{
  const s = slide(); addTitle(s,'Your teaching pack','The deck and runnable examples use the same sample document.');
  card(s,0.8,1.45,7.25,4.9,'0C1927','23435B');
  s.addText('Python files', { x:1.1,y:1.76,w:2.0,h:0.3,fontSize:14,bold:true,color:C.cyan,margin:0 });
  const files=[
    'fixed_size_chunking.py','sliding_window_chunking.py','sentence_paragraph_chunking.py','recursive_chunking.py',
    'semantic_chunking.py','hierarchical_chunking.py','parent_child_chunking.py','structure_aware_chunking.py',
    'agentic_chunking.py','proposition_chunking.py','late_chunking_demo.py','compare_chunkers.py'
  ];
  files.forEach((f,i)=>{
    const col=i<6?0:1; const row=i%6;
    s.addText('• '+f,{x:1.08+col*3.4,y:2.28+row*0.48,w:3.25,h:0.24,fontFace:'Aptos Mono',fontSize:9.7,color:i===11?C.green:C.text,margin:0,fit:'shrink'});
  });
  s.addText('sample_policy.txt  ·  README.md  ·  requirements.txt',{x:1.12,y:5.58,w:6.4,h:0.27,fontFace:'Aptos Mono',fontSize:9.3,color:C.muted,margin:0});
  card(s,8.45,1.45,4.1,2.02,'0F1D2E',C.green);
  s.addText('Run the lightweight demos',{x:8.75,y:1.77,w:3.5,h:0.26,fontSize:12,bold:true,color:C.green,margin:0});
  codeBlock(s,8.73,2.14,3.52,0.9,'python compare_chunkers.py');
  card(s,8.45,3.78,4.1,2.07,'0F1D2E',C.purple);
  s.addText('Embedding-based demos',{x:8.75,y:4.08,w:3.45,h:0.26,fontSize:12,bold:true,color:C.purple,margin:0});
  codeBlock(s,8.73,4.43,3.52,1.05,'pip install -r requirements.txt\npython semantic_chunking.py');
  teachBox(s,8.45,6.1,4.1,'Suggested class activity: let learners predict boundaries first, then run the scripts.',C.cyan);
}

pptx.writeFile({ fileName: '/mnt/data/chunking_teaching_pack/Chunking_Strategies_for_RAG.pptx' });
