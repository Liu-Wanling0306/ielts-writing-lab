'use strict';
const DATA=window.IELTS_DATA;
const CONNECTOR_LIBRARY=window.IELTS_DATA.connectorLibrary;
const VERSION='1.4.1';
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const keyName=(...s)=>'ieltsLab:'+s.join(':');
const store={get(k,def=null){try{let v=localStorage.getItem(k);return v===null?def:JSON.parse(v)}catch(e){return def}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v));return true}catch(e){return false}}};
const USER=store.get(keyName('user'),{answers:{},drafts:{},completed:{},review:{},extraErrors:[],snapshots:[]});
function saveUser(){store.set(keyName('user'),USER);$('#progressCount').textContent=Object.keys(USER.completed||{}).length}
let page='home';let state={task2:'t2-23',task1:'t1-01',step:'read',version:{},reveal:{}};
function go(p){page=p;$$('.page').forEach(x=>x.classList.toggle('active',x.id===p));$$('.nav button').forEach(x=>x.classList.toggle('active',x.dataset.page===p));if(p==='versions')renderVersions();if(p==='errors')renderErrors(false);window.scrollTo({top:0,behavior:'instant'})}
$$('.nav button').forEach(x=>x.addEventListener('click',()=>go(x.dataset.page)));
$('#toVersions').onclick=e=>{e.preventDefault();go('versions')};
function taskEntries(prefix){return DATA.articles.filter(a=>a.id.startsWith(prefix))}
function currentArticle(type){return DATA.articles.find(x=>x.id===state[type])}
function getEdition(a){return state.version[a.id]||a.preferred}
function paras(a){return a[getEdition(a)==='seven'?'source_seven':'source_nine']}
function sectionName(a,i,n){if(a.type==='小作文')return i===0?'Introduction':i===1?'Overview':i===2?'Detail 1':i===3?'Detail 2':'Detail '+(i-1);return i===0?'Introduction':i===n-1?'Conclusion':'Body '+i}
function initCatalog(type){let is2=type==='task2', suffix=is2?'2':'1';let all=taskEntries(is2?'t2':'t1');let cat=$('#category'+suffix);cat.innerHTML='<option value="">全部主题 / 题型</option>'+[...new Set(all.map(x=>x.group))].map(x=>'<option>'+esc(x)+'</option>').join('');$('#search'+suffix).oninput=()=>renderCatalog(type);cat.onchange=()=>renderCatalog(type);renderCatalog(type)}
function renderCatalog(type){let is2=type==='task2',suffix=is2?'2':'1';let all=taskEntries(is2?'t2':'t1');let query=$('#search'+suffix).value.trim().toLowerCase(),category=$('#category'+suffix).value;let visible=all.filter(a=>(!category||a.group===category)&&(!query||(a.title+' '+a.question+' '+a.group).toLowerCase().includes(query)));$('#list'+suffix).innerHTML=visible.length?visible.map(a=>`<div class="item ${state[type]===a.id?'active':''}" role="button" tabindex="0" data-pick="${a.id}"><b>${esc(a.id.split('-')[1])} · ${esc(a.title)}</b><div class="meta">${esc(a.group)} · ${a.edition_labels?esc(a.edition_labels.nine):a.type==='小作文'?'9 分完整版':a.meta.seven_complete?'7+ / 9 分完整版':'完整 9 分版'}</div></div>`).join(''):'<p class="muted small">没有找到匹配题目</p>';$$('#list'+suffix+' .item').forEach(el=>{let act=()=>{state[type]=el.dataset.pick;state.step='read';renderCatalog(type);renderLesson(type)};el.onclick=act;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act()}}})}
function setEdition(a,ed,type){if(!(a.meta[ed+'_complete']))return;state.version[a.id]=ed;state.step='read';renderLesson(type)}
function setStep(step,type){state.step=step;renderLesson(type);$('#lesson'+(type==='task2'?'2':'1')).scrollIntoView({behavior:'smooth',block:'start'})}
function splitLogic(logic){return logic.split(/\s*[▪•]\s*/).filter(Boolean).map(x=>x.trim()).slice(0,6)}
function readHighlight(p){let marks=(p.clozes||[]).filter(c=>c.answer.length<65).sort((a,b)=>a.start-b.start).slice(0,6);let out='',pos=0,idx=0;for(let m of marks){if(m.start<pos||m.end>p.en.length)continue;out+=esc(p.en.slice(pos,m.start));let kind=/^(however|nevertheless|although|whereas|by contrast|as a result|in contrast|on the other hand|for example|in addition|therefore)/i.test(m.answer)?'link':/^(accounted for|the figure for|fell|rose|the largest|the lowest)/i.test(m.answer)?'struct':idx%2===0?'topic':'effect';out+=`<mark class="hl hl-${kind}" title="重点搭配">${esc(m.answer)}</mark>`;pos=m.end;idx++}return out+esc(p.en.slice(pos))}
function readStep(a,ps){let logic=splitLogic(a.logic).map(x=>'<div class="logicline">'+esc(x)+'</div>').join('');let vocabs=a.vocab?.length?`<details><summary>原材料高分表达 · ${a.vocab.length} 条</summary><div class="kblist">${a.vocab.map(v=>`<div class="kb"><b>${esc(v.en)}</b><br><span class="muted small">${esc(v.zh)}</span></div>`).join('')}</div></details>`:'<p class="muted small">本篇未单列高分表达表，已根据段落中的实际搭配进行高亮。</p>';
return `<div class="subcard"><h4>原文核心逻辑链</h4>${logic}</div><div class="rule"></div><div class="row spread"><h3>完整范文 · ${ps.length} 段</h3><div class="legend"><span class="hl hl-topic">重点搭配</span><span class="hl hl-link">连接与转折</span><span class="hl hl-effect">机制与结果</span><span class="hl hl-struct">数据描述</span></div></div><p class="small muted">淡色标注是源文中的真实表达；绿色、蓝色和暖金色仅帮助区分功能，不代表 IELTS 官方评分。</p>${ps.map((p,i)=>`<article class="modelp"><div class="row spread"><b>${sectionName(a,i,ps.length)}</b><span class="muted small">${p.en.split(/\s+/).length} words</span></div><p class="en" lang="en">${readHighlight(p)}</p><details><summary>查看该段原文中文译文</summary><div class="cn">${esc(p.cn||'本段未提取到中文译文。')}</div></details></article>`).join('')}<div class="rule"></div>${vocabs}<div class="actions"><button class="primary" onclick="setStep('cloze','${a.type==='小作文'?'task1':'task2'}')">下一步：全文搭配挖空</button></div>`}
function normalize(s){return String(s||'').normalize('NFKC').toLowerCase().replace(/[’‘]/g,"'").replace(/[“”]/g,'"').replace(/[^a-z0-9]+/g,' ').trim().replace(/\s+/g,' ')}
function fullTargets(ps){return ps.map((p,i)=>({p,i}))}
function paragraphClozes(p){
 let original=(p.clozes||[]).filter(c=>Number.isInteger(c.start)&&c.start>=0&&c.end>c.start&&p.en.slice(c.start,c.end)===c.answer).sort((a,b)=>a.start-b.start);
 if(original.length)return original;
 const candidates=[/\b(?:compares?|illustrates?|shows?|describes?)\b/i,/\b(?:employment rates?|the proportion of|the percentage of|the number of|by contrast|in conclusion|overall|as a result|compared with|rather than|is then|are then)\b/i];
 let match=candidates.map(r=>r.exec(p.en)).find(Boolean);
 if(!match)match=/\b[A-Za-z]+(?:[ ’'-]+[A-Za-z]+){1,3}/.exec(p.en);
 return match?[{start:match.index,end:match.index+match[0].length,answer:match[0]}]:[];
}
function clozeStep(a,ps){let group=fullTargets(ps);let blocks=group.map(({p,i})=>{let items=paragraphClozes(p).slice(0,7),html='',pos=0;items.forEach((g,j)=>{if(g.start<pos)return;html+=esc(p.en.slice(pos,g.start));let id=`${a.id}|${getEdition(a)}|${i}|${j}`,value=USER.answers[id]||'';html+=`<input class="blankinput" data-cloze="${esc(id)}" data-answer="${esc(g.answer)}" value="${esc(value)}" style="width:${Math.min(310,Math.max(120,g.answer.length*9))}px" aria-label="第 ${j+1} 空" placeholder="第${j+1}空">`;pos=g.end});html+=esc(p.en.slice(pos));return `<article class="clozebox"><h4>${sectionName(a,i,ps.length)} · ${items.length} 处搭配</h4><p class="en" lang="en">${html}</p><div class="actions"><button class="mini" onclick="checkCloze('${a.id}',${i})">检查本段</button><button class="mini" onclick="toggleAnswer('cloze-${a.id}-${i}')">查看完整参考段落</button></div><div id="result-${a.id}-${i}" class="feedback small"></div><div class="answer" id="cloze-${a.id}-${i}"><div class="en" lang="en">${esc(p.en)}</div></div></article>`}).join('');return `<p class="muted">全文共 ${ps.length} 段，包含引言和结尾（如有）。按照源范文中的原词组填空。自动检查只判断是否与参考搭配一致，合理同义表达需要你自己结合语境判断。</p>${blocks||'<p>此版本未能识别合适的填空表达，请先练习中文翻译。</p>'}<div class="actions"><button class="primary" onclick="setStep('translate','${a.type==='小作文'?'task1':'task2'}')">下一步：中译英训练</button></div>`}
function checkCloze(articleId,i){let sels=$$(`input[data-cloze^="${articleId}|"]`).filter(el=>el.dataset.cloze.split('|')[2]==String(i));let correct=0;sels.forEach(el=>{let ok=normalize(el.value)===normalize(el.dataset.answer);el.classList.remove('ok','bad');el.classList.add(ok?'ok':'bad');if(ok)correct++});$('#result-'+articleId+'-'+i).textContent=`本段严格匹配 ${correct}/${sels.length}，红色标记可对照原段核查。`;if(sels.length&&correct===sels.length){USER.completed[articleId+':cloze:'+i]=true;saveUser()}}
function toggleAnswer(id){let x=document.getElementById(id);if(x)x.classList.toggle('show')}
function translateStep(a,ps){let group=fullTargets(ps);let blocks=group.map(({p,i})=>{let id=`tr:${a.id}:${getEdition(a)}:${i}`;return `<article class="clozebox"><h4>${sectionName(a,i,ps.length)} · 原文中译英</h4><p class="translation-cn">${esc(p.cn||'本段缺少中文译文，请查看英文参考。')}</p><label class="small muted" for="${id}">你的英文重写（可用不同表达，但要保留事实和因果关系）</label><textarea lang="en" id="${id}" data-draft="${esc(id)}" placeholder="先不看答案写英文段落，再比较信息、搭配、冠词和时态。">${esc(USER.drafts[id]||'')}</textarea><div class="row spread"><span class="muted small">已输入 <span id="wc-${id}">${(USER.drafts[id]||'').trim().split(/\s+/).filter(Boolean).length}</span> 词</span><button class="mini" onclick="toggleAnswer('trans-${a.id}-${i}')">查看完整英文参考</button></div><div class="answer" id="trans-${a.id}-${i}"><p class="en">${esc(p.en)}</p><p class="small muted">注意：译文仅有一种参考写法，不是唯一正确答案；本网页不提供 AI 自动评分。</p></div></article>`}).join('');return `<p class="muted">全文共 ${ps.length} 段。利用材料中对应段落的中文译文主动写英文，再对照原文检查中心句、逻辑关系、数据和搭配。</p>${blocks}<div class="actions"><button class="primary" onclick="setStep('transfer','${a.type==='小作文'?'task1':'task2'}')">下一步：重点搭配迁移</button></div>`}
function transferStep(a,ps){
 const exercises=a.transfer?.[getEdition(a)]||[];
 return `<p class="muted">把本篇重点搭配用于新的话题或数据。先翻译中文，再查看参考答案；例句为迁移练习编写，不代表原图数据。</p>${exercises.map((x,i)=>{
 const id=`transfer:${a.id}:${getEdition(a)}:${x.id}`;
 return `<article class="clozebox" data-transfer-item><h4>${i+1} · <span lang="en">${esc(x.phrase)}</span></h4><details><summary>查看范文中的搭配出处</summary><p class="en" lang="en">${esc(x.source)}</p></details><p class="translation-cn">${esc(x.cn)}</p><label for="${id}" class="small muted">请用上方搭配翻译这个新例句，可按语境调整词形</label><textarea id="${id}" lang="en" data-draft="${id}" placeholder="将搭配用到新情境中……">${esc(USER.drafts[id]||'')}</textarea><div class="actions"><button class="mini" onclick="toggleAnswer('answer-${id}')">查看参考答案</button></div><div class="answer" id="answer-${id}"><p class="en" lang="en">${esc(x.answer)}</p><p class="small muted">这是一种参考写法。核对搭配、词形和题目信息，合理同义表达也可以。</p></div></article>`;
 }).join('')||'<p class="note">本版本暂无迁移题。</p>'}<div class="actions"><button class="primary" onclick="markLessonDone('${a.id}')">完成本篇训练</button><button onclick="setStep('read','${a.type==='小作文'?'task1':'task2'}')">返回范文拆解</button></div>`;
}
// Chart images are kept separately from text drafts to avoid localStorage quota limits.
let chartDBPromise;
const chartURLs=new Map();
function chartDB(){
 if(!chartDBPromise)chartDBPromise=new Promise((resolve,reject)=>{
  const request=indexedDB.open('ieltsLabCharts',1);
  request.onupgradeneeded=()=>request.result.createObjectStore('charts',{keyPath:'id'});
  request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);
 });
 return chartDBPromise;
}
async function chartStore(mode,action){
 const db=await chartDB();
 return new Promise((resolve,reject)=>{const tx=db.transaction('charts',mode);const req=action(tx.objectStore('charts'));tx.oncomplete=()=>resolve(req.result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error||Error('保存中断'));});
}
function chartPanel(a){return `<aside class="chart-box" aria-label="本题图表"><h3>题目图表</h3><div id="chart-preview-${a.id}" class="chart-preview"><span class="muted small">可上传本题的数据图、地图或流程图</span></div><label class="chart-upload" for="chart-file-${a.id}">上传 / 更换图表</label><input id="chart-file-${a.id}" type="file" accept="image/png,image/jpeg,image/webp,image/gif" onchange="uploadChart('${a.id}',this)"><button class="mini" id="chart-remove-${a.id}" hidden onclick="removeChart('${a.id}')">移除图表</button><p id="chart-status-${a.id}" class="small muted" role="status">按题目保存在当前浏览器，可通过“导出备份”带走图片。</p></aside>`}
async function showChart(id){
 const preview=document.getElementById('chart-preview-'+id);if(!preview)return;
 try{
  const record=await chartStore('readonly',store=>store.get(id));
  if(!preview.isConnected)return;
  const old=chartURLs.get(id);if(old){URL.revokeObjectURL(old);chartURLs.delete(id)}
  const remove=document.getElementById('chart-remove-'+id);if(remove)remove.hidden=!record;
  preview.replaceChildren();
  if(!record){const note=document.createElement('span');note.className='muted small';note.textContent='可上传本题的数据图、地图或流程图';preview.append(note);return}
  const url=URL.createObjectURL(record.blob);chartURLs.set(id,url);
  const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener';link.title='打开完整图表';
  const img=document.createElement('img');img.src=url;img.alt='本题图表：'+record.name;link.append(img);preview.append(link);
 }catch(e){const status=document.getElementById('chart-status-'+id);if(status)status.textContent='图片存储不可用，请检查浏览器的存储设置。'}
}
async function uploadChart(id,input){
 const file=input.files?.[0];if(!file)return;
 const status=document.getElementById('chart-status-'+id);
 try{
  if(!['image/png','image/jpeg','image/webp','image/gif'].includes(file.type))throw Error('请选择 PNG、JPEG、WebP 或 GIF 图片。');
  if(file.size>10*1024*1024)throw Error('单张图片请小于 10 MB。');
  const bitmap=await createImageBitmap(file);bitmap.close();
  await chartStore('readwrite',store=>store.put({id,name:file.name,blob:file}));
  await showChart(id);if(status.isConnected)status.textContent='图表已保存到当前浏览器。点击图片可查看完整图表；导出备份可包含图片。';
 }catch(e){if(status.isConnected)status.textContent='上传失败：'+e.message}
 input.value='';
}
async function removeChart(id){try{await chartStore('readwrite',store=>store.delete(id));await showChart(id);const status=document.getElementById('chart-status-'+id);if(status)status.textContent='已移除本题图表。'}catch(e){alert('移除失败：'+e.message)}}
function blobDataURL(blob){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=()=>reject(r.error);r.readAsDataURL(blob)})}
function markLessonDone(id){USER.completed[id+':finished']=true;saveUser();alert('本篇已标记完成。建议用同一套搭配再独立写一段。')}
function renderLesson(type){let a=currentArticle(type),ps=paras(a);let is2=a.type==='大作文',ed=getEdition(a);let lessons=['read','cloze','translate','transfer'];let names=['01 范文拆解','02 搭配挖空','03 中译英','04 搭配迁移'];let buttons=lessons.map((s,i)=>`<button class="${state.step===s?'active':''}" onclick="setStep('${s}','${type}')">${names[i]}</button>`).join('');let edopt=a.edition_labels?`<div class="row"><label class="small muted">参考版本</label>${['seven','nine'].filter(v=>a.meta[v+'_complete']).map(v=>`<button class="mini ${ed===v?'active':''}" onclick="setEdition(DATA.articles.find(x=>x.id==='${a.id}'),'${v}','${type}')">${esc(a.edition_labels[v])}</button>`).join('')}</div>`:is2?`<div class="row"><label class="small muted">来源版本</label><button class="mini ${ed==='seven'?'active':''}" ${a.meta.seven_complete?'':'disabled'} onclick="setEdition(DATA.articles.find(x=>x.id==='${a.id}'),'seven','${type}')">7+ 稳定版 ${!a.meta.seven_complete?'(不完整)':''}</button><button class="mini ${ed==='nine'?'active':''}" ${a.meta.nine_complete?'':'disabled'} onclick="setEdition(DATA.articles.find(x=>x.id==='${a.id}'),'nine','${type}')">9 分进阶版</button></div>`:'<p class="small muted">源资料仅提供 9 分命名版本 · 仅用于学习表达与组织</p>';let note=a.source_note?`<div class="note">${esc(a.source_note)}</div>`:'';
let body=state.step==='read'?readStep(a,ps):state.step==='cloze'?clozeStep(a,ps):state.step==='translate'?translateStep(a,ps):transferStep(a,ps);
let target=document.getElementById('lesson'+(type==='task2'?'2':'1'));target.innerHTML=`<div class="card"><div class="row spread"><span class="pill">${esc(a.group)} · ${a.type==='大作文'?'Task 2':'Task 1'}</span><span class="muted small">${esc(a.id.toUpperCase())}</span></div><div class="question-layout"><div><h2 style="margin-top:11px">${esc(a.title)}</h2><div class="question" lang="en">${esc(a.question)}</div></div>${is2?'':chartPanel(a)}</div><div class="rule"></div>${edopt}${note}${a.type==='小作文'?'<div class="note">注意：练习用原 PDF 范文文字整理，未必包含原始图表；真实数据与单位需以题目图片为准。</div>':''}<div class="step-tabs">${buttons}</div><div id="stepContent">${body}</div></div>`;
if(!is2)showChart(a.id);
// persist inputs of active step, without rerender on keystrokes.
target.querySelectorAll('input[data-cloze]').forEach(el=>el.addEventListener('input',()=>{USER.answers[el.dataset.cloze]=el.value;saveUser()}));target.querySelectorAll('textarea[data-draft]').forEach(el=>el.addEventListener('input',()=>{USER.drafts[el.dataset.draft]=el.value;let count=(el.value.trim().match(/\S+/g)||[]).length;let out=document.getElementById('wc-'+el.dataset.draft);if(out)out.textContent=count;saveUser()}));}
function renderConnectors(){
 let cont=$('#connectorList');
 const makeLines=(g,kind='struct')=>`<div class="cx-card"><h4>${esc(g.title)}</h4><div class="cx-use">${esc(g.use||'')}</div>${g.lines.map(x=>`<div class="cx-line" data-search="${esc([x.en,x.cn,x.tip||'',g.title].join(' ').toLowerCase())}"><div class="cx-en"><span class="cx-highlight ${kind==='link'?'cx-link':''}">${esc(x.en)}</span></div><div class="cx-cn">${esc(x.cn)}</div>${x.tip?`<div class="cx-tip">${esc(x.tip)}</div>`:''}</div>`).join('')}</div>`;
 const section=(title,desc,items,kind='struct')=>`<section class="cx-section"><h3>${title}</h3><p class="muted small">${desc}</p><div class="cx-grid">${items.map(x=>makeLines(x,kind)).join('')}</div></section>`;
 const topicMarkup=CONNECTOR_LIBRARY.topics.map((t,i)=>`<details class="cx-topic" data-topic-card><summary>${esc(t.name)} <span class="cx-count">正面 ${t.positive.length} 条 · 负面 ${t.negative.length} 条</span></summary><div class="cx-tone-title good">✓ 正面观点与收益表达</div><div class="cx-grid">${t.positive.map(x=>`<article class="cx-expression" data-expression data-search="${esc([t.name,x.phrase,x.cn,x.example].join(' ').toLowerCase())}"><span class="phrase good">${esc(x.phrase)}</span><div class="translation">${esc(x.cn)}</div><div class="example">${esc(x.example)}</div></article>`).join('')}</div><div class="cx-tone-title bad">− 负面观点与风险表达</div><div class="cx-grid">${t.negative.map(x=>`<article class="cx-expression" data-expression data-search="${esc([t.name,x.phrase,x.cn,x.example].join(' ').toLowerCase())}"><span class="phrase bad">${esc(x.phrase)}</span><div class="translation">${esc(x.cn)}</div><div class="example">${esc(x.example)}</div></article>`).join('')}</div></details>`).join('');
 const legacy=DATA.connectors.map((c,i)=>`<div class="clozebox" data-search="${esc(c.join(' ').toLowerCase())}"><div class="row spread"><b>${esc(c[0])}</b><button class="mini" onclick="toggleAnswer('conn-${i}')">查看参考表达</button></div><p class="muted small">先尝试写出一个适合该功能的完整英文例句。</p><textarea lang="en" data-connector="${i}" rows="2" style="min-height:74px" placeholder="尝试独立写一句，注意不要叠加重复衔接词。">${esc(USER.drafts['conn:'+i]||'')}</textarea><div class="answer" id="conn-${i}"><b>${esc(c[1])}</b><p class="en">${esc(c[2])}</p></div></div>`).join('');
 cont.innerHTML=`<div class="cx-intro"><b>使用原则：</b>每段通常选择 1–2 个清晰的逻辑连接方式即可。优先用准确的主谓结构、因果关系和比较关系建立衔接，不要在每句话开头机械添加连接词。<div class="legend" style="margin-top:8px"><span><span class="hl hl-struct">蓝色</span> 句型模板</span><span><span class="hl hl-link">紫色</span> 逻辑衔接</span><span><span class="hl" style="background:#eaf4ec;color:#2d6848">绿色</span> 正面搭配</span><span><span class="hl" style="background:#fff0ed;color:#a45149">暖红</span> 负面搭配</span></div></div>
 <input class="cx-search" id="cxSearch" type="search" placeholder="搜索英文搭配 / 中文含义 / 话题，例如：financial burden、教育不平等……" oninput="filterConnectorCards(this.value)">
 <div class="cx-tabs"><button class="active" data-cx-tab="templates" onclick="showConnectorTab('templates')">开头、中心句与结尾模板</button><button data-cx-tab="logic" onclick="showConnectorTab('logic')">逻辑衔接表达</button><button data-cx-tab="topics" onclick="showConnectorTab('topics')">话题正反高分搭配</button><button data-cx-tab="task1" onclick="showConnectorTab('task1')">Task 1 数据衔接</button></div>
 <div class="cx-panel active" id="cx-templates">${section('一、开头段模板','按题型选择表达。方括号内容需要替换成题目中的具体信息。',CONNECTOR_LIBRARY.openings)}${section('二、主体段中心句模板','中心句负责明确本段论点；后续再解释机制、举例并落到结果。',CONNECTOR_LIBRARY.body)}${section('三、结尾段模板','结尾应回答题目、重申立场或总结措施，不要机械重复主体段所有细节。',CONNECTOR_LIBRARY.conclusions)}</div>
 <div class="cx-panel" id="cx-logic">${section('逻辑连接与论证推进','每组提供多种可替换表达。注意连接词后面的语法结构。',CONNECTOR_LIBRARY.logic,'link')}<div class="cx-legacy"><details><summary>展开原有衔接词例句练习（保留你的历史输入）</summary>${legacy}</details></div></div>
 <div class="cx-panel" id="cx-topics"><h3>不同话题的正反观点高分搭配</h3><p class="muted small">共 ${CONNECTOR_LIBRARY.topics.length} 个话题；每个话题提供至少 6 条正面表达和 6 条负面表达。建议先遮住中文和例句，尝试自己造句，再展开核对。</p>${topicMarkup}</div>
 <div class="cx-panel" id="cx-task1">${section('Task 1｜Overview 与数据段衔接','小作文连接表达应服务于分组、比较和趋势描述，不要加入主观评价。',CONNECTOR_LIBRARY.task1,'link')}</div>
 <p class="small muted" id="cxSearchCount" aria-live="polite"></p>`;
 $$('#connectorList textarea[data-connector]').forEach(el=>el.oninput=()=>{USER.drafts['conn:'+el.dataset.connector]=el.value;saveUser()});
}
function showConnectorTab(name){$$('#connectorList .cx-panel').forEach(x=>x.classList.toggle('active',x.id==='cx-'+name));$$('#connectorList [data-cx-tab]').forEach(x=>x.classList.toggle('active',x.dataset.cxTab===name));}
function filterConnectorCards(value){let q=(value||'').trim().toLowerCase();let nodes=$$('#connectorList [data-search]');let visible=0,counts={};nodes.forEach(el=>{let ok=!q||(el.dataset.search||'').includes(q);el.classList.toggle('cx-filter-hidden',!ok);if(ok){visible++;let panel=el.closest('.cx-panel');if(panel)counts[panel.id]=(counts[panel.id]||0)+1}});$$('#connectorList [data-topic-card]').forEach(d=>{let any=[...d.querySelectorAll('[data-expression]')].some(x=>!x.classList.contains('cx-filter-hidden'));d.classList.toggle('cx-filter-hidden',q&&!any);if(q&&any)d.open=true});if(q){let active=$('#connectorList .cx-panel.active')?.id;if(!counts[active]){let best=Object.entries(counts).sort((a,b)=>b[1]-a[1])[0];if(best)showConnectorTab(best[0].replace('cx-',''))}}let out=$('#cxSearchCount');if(out)out.textContent=q?`找到 ${visible} 条匹配表达；已自动切换到匹配最多的分类。`:''}
function renderErrors(onlyReview){let all=[...DATA.errors,...(USER.extraErrors||[])];let filtered=all.map((e,i)=>({e,i})).filter(({i})=>!onlyReview||USER.review[i]);$('#errorList').innerHTML=filtered.length?filtered.map(({e,i})=>`<div class="clozebox"><div class="row spread"><span class="muted small">${i+1} · 个人错题</span><button class="mini ${USER.review[i]?'active':''}" onclick="toggleReview(${i},${onlyReview})">${USER.review[i]?'待复习 ✓':'标记待复习'}</button></div><p><s style="color:#a15b5b">${esc(e[0])}</s> <span class="muted">→ 请先回忆正确搭配</span></p><input type="text" data-error="${i}" style="width:min(100%,490px)" placeholder="输入正确表达" value="${esc(USER.answers['err:'+i]||'')}"><button class="mini" onclick="checkError(${i})">核对</button><button class="mini" onclick="toggleAnswer('error-${i}')">看答案与讲解</button><span class="feedback small" id="error-result-${i}"></span><div class="answer" id="error-${i}"><b>${esc(e[1])}</b><p>${esc(e[2])}</p><p class="en">${esc(e[3])}</p></div></div>`).join(''):'<p class="muted">当前没有标记待复习的错题。</p>';$$('#errorList input[data-error]').forEach(el=>el.oninput=()=>{USER.answers['err:'+el.dataset.error]=el.value;saveUser()})}
function toggleReview(i,flag){USER.review[i]=!USER.review[i];saveUser();renderErrors(flag)}
function checkError(i){let e=[...DATA.errors,...(USER.extraErrors||[])][i];let ok=normalize(USER.answers['err:'+i])===normalize(e[1]);$('#error-result-'+i).textContent=ok?'✓ 与参考搭配一致':'请再检查介词、冠词、词形，或查看答案。';if(ok){USER.completed['error:'+i]=true;saveUser()}}
function addError(){let bad=$('#newWrong').value.trim(),good=$('#newCorrect').value.trim(),note=$('#newExplain').value.trim();if(!bad||!good){alert('请先填写错误和正确表达');return}USER.extraErrors.push([bad,good,note,'']);saveUser();['#newWrong','#newCorrect','#newExplain'].forEach(s=>$(s).value='');renderErrors(false)}
function renderArchive(){let el=$('#essayArchive');el.innerHTML=DATA.essays.map((a,i)=>`<div class="archive"><h3>${esc(a.title)}</h3><span class="pill">${esc(a.type)}</span><details><summary>查看你提交的原稿</summary><pre>${esc(a.original)}</pre></details><details><summary>查看本次主要纠错记录</summary><div class="subcard">${esc(a.feedback)}</div></details>${a.model?`<details><summary>${a.model.includes('见本项目原对话')?'修订稿说明':'已保存的参考修订稿'}</summary><pre>${esc(a.model)}</pre></details>`:''}</div>`).join('')}
const BASE={version:'1.1.0',date:'2026-11-14',items:['Task 1：30 篇题目索引','Task 2：40 篇题目索引','6 个主题主体段搭配填空','个人作文档案','原 PDF 逐页文字检索','衔接词与功能搭配列表','浏览器本地 JSON 快照与功能 Diff']};
const PREVIOUS={version:'1.2.0',date:'2026-11-14',items:['70 篇按题目与段落整理的范文','Task 2：39 篇完整 7+ 版与 40 篇 9 分版','Task 1：30 篇 9 分命名版完整文本','来源残缺版本标记与完整版本切换','结构化逻辑链与中英对照','范文表达柔和高亮','每篇主体段 / Overview 搭配挖空','每篇中文译英与段落重组','个人语法与搭配错题循环','个人作文档案','浏览器本地答案保存与 JSON 备份','版本快照与 GitHub-style 功能清单 Diff']};
const RELEASE_13={version:'1.3.0',date:'2026-11-14',items:['保留 v1.2.0 大作文与小作文训练框架','新增 6 类开头段模板，覆盖常见 Task 2 题型','新增 10 组主体段中心句模板','新增 10 组逻辑衔接表达，每组多种替换句型','新增 6 类结尾段模板','新增 12 个高频话题正反观点搭配库，每类各 6 条','每条话题搭配提供中文释义与完整例句','新增 Task 1 Overview、趋势、比较、地图流程衔接表达','衔接搭配库支持中英文关键词检索','保留原有衔接词练习与用户输入记录','版本 Diff 新增 v1.2.0 → v1.3.0 对照','兼容原有浏览器本地训练进度与 JSON 备份']};
const CURRENT={version:VERSION,date:'2026-11-15',items:[...RELEASE_13.items,'72篇文章的全文填空与翻译，保留引言、全部主体段和结尾','第4模块改为重点搭配迁移翻译，提供新情境题目、搭配出处和参考答案','每道小作文支持图表上传、预览、按题保存和备份恢复','新增T2-41外语小班教学：完整四段参考稿、12条搭配迁移、个人批改与错题']};
function versions(){return [BASE,PREVIOUS,RELEASE_13,CURRENT,...(USER.snapshots||[])]}
function renderVersions(){let v=versions();let label=i=>i===0?'· 初始版':i===2?'· 上一版':i===3?'· 最新版':'';$('#oldVersion').innerHTML=v.map((x,i)=>`<option value="${i}">${esc(x.version)} ${label(i)}</option>`).join('');$('#newVersion').innerHTML=v.map((x,i)=>`<option value="${i}">${esc(x.version)} ${label(i)}</option>`).join('');$('#oldVersion').value='2';$('#newVersion').value='3';showDiff()}
function showDiff(){let v=versions(),a=v[Number($('#oldVersion').value)]||PREVIOUS,b=v[Number($('#newVersion').value)]||CURRENT;let removed=a.items.filter(x=>!b.items.includes(x)),added=b.items.filter(x=>!a.items.includes(x)),unchanged=b.items.filter(x=>a.items.includes(x));let info=`<p><b>${esc(a.version)} → ${esc(b.version)}</b> · 新增 ${added.length} 项 / 删除 ${removed.length} 项 / 保留 ${unchanged.length} 项</p>`;let lines=[...removed.map(x=>`<span class="del">- ${esc(x)}</span>`),...added.map(x=>`<span class="add">+ ${esc(x)}</span>`),...unchanged.map(x=>`<span class="same">  ${esc(x)}</span>`)];$('#diffResult').innerHTML=info+'<div class="versiondiff">'+(lines.join('')||'两个版本无差异')+'</div>'}
function saveSnapshot(){let snap={...CURRENT,version:VERSION+'-snapshot-'+(USER.snapshots.length+1),date:new Date().toISOString()};USER.snapshots.push(snap);saveUser();renderVersions()}
async function exportBackup(){
 try{
  const records=await chartStore('readonly',store=>store.getAll());
  const charts=await Promise.all(records.map(async r=>({id:r.id,name:r.name,data:await blobDataURL(r.blob)})));
  const blob=new Blob([JSON.stringify({schema:'IELTS-WRITING-LAB-v1.4',version:VERSION,exported:new Date().toISOString(),user:USER,charts,versions:versions()},null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`IELTS_Writing_Lab_v${VERSION}_backup.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);
 }catch(e){alert('备份失败：'+e.message+'。请检查浏览器图片存储是否可用。')}
}
async function importBackup(event){
 const f=event.target.files?.[0];if(!f)return;
 try{
  const obj=JSON.parse(await f.text());if(!obj.user||typeof obj.user!=='object'||!obj.user.answers||!obj.user.drafts)throw Error('无效的训练记录 JSON');
  const charts=[];
  for(const record of obj.charts||[]){
   if(!DATA.articles.some(a=>a.id===record.id&&a.type==='小作文')||!/^data:image\/(png|jpeg|webp|gif);base64,/.test(record.data))throw Error('备份含无效的图表记录');
   const blob=await (await fetch(record.data)).blob();if(blob.size>10*1024*1024)throw Error('备份图表超过10 MB');
   const bitmap=await createImageBitmap(blob);bitmap.close();charts.push({id:record.id,name:record.name||'题目图表',blob});
  }
  if(charts.length)await chartStore('readwrite',store=>{let req;for(const r of charts)req=store.put(r);return req});
  for(let k of ['answers','drafts','completed','review'])USER[k]={...(USER[k]||{}),...(obj.user[k]||{})};
  USER.extraErrors=obj.user.extraErrors||USER.extraErrors;USER.snapshots=obj.user.snapshots||USER.snapshots;saveUser();renderVersions();
  renderLesson('task1');renderLesson('task2');alert(`训练记录已导入，恢复 ${charts.length} 张图表。`);
 }catch(e){alert('导入失败：'+e.message)}
 event.target.value='';
}
initCatalog('task2');initCatalog('task1');renderLesson('task2');renderLesson('task1');renderConnectors();renderArchive();renderVersions();saveUser();
