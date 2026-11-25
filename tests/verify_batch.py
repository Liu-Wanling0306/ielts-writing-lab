"""Exercise-1 import: full coverage, source fidelity, drafts and mobile layout."""
import asyncio,json,os,shutil
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path=shutil.which('chromium'))
  page=await browser.new_page(ignore_https_errors=True)
  await page.add_init_script("localStorage.setItem('ielts-gate','1')")
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(os.environ.get('IELTS_TEST_URL','http://127.0.0.1:8021'))
  await page.wait_for_selector('#lesson2 .step-tabs',state='attached')
  result=await page.evaluate('''()=>{let count=0;for(let i=43;i<=51;i++){const a=DATA.articles.find(a=>a.id==='t2-'+i);if(!a)throw Error('Missing article');openArticle(a.id);for(const ed of ['seven','nine']){setEdition(a,ed,'task2');const ps=paras(a);if(ps.length!==4)throw Error('Paragraphs');for(const step of ['read','cloze','translate','transfer']){setStep(step,'task2');const root=document.querySelector('#lesson2 #stepContent');if(step==='read'){if(root.querySelectorAll('.modelp').length!==4||root.querySelectorAll('[data-review-drill]').length!==3)throw Error('Reading');if(root.textContent.includes('原稿练习估分'))throw Error('Invented scoring')}if(step==='cloze'){const blocks=root.querySelectorAll('.clozebox');if(blocks.length!==4)throw Error('Cloze blocks');blocks.forEach((b,n)=>{let para=b.querySelector('p.en').cloneNode(true);para.querySelectorAll('input').forEach(x=>x.replaceWith(x.dataset.answer));if(para.textContent!==ps[n].en)throw Error('Cloze source mismatch')})}if(step==='translate'){const cs=root.querySelectorAll('.translation-cn');if(cs.length!==4)throw Error('CN missing');cs.forEach((c,n)=>{if(c.textContent!==ps[n].cn)throw Error('CN mismatch')})}if(step==='transfer'&&root.querySelectorAll('[data-transfer-item]').length!==8)throw Error('Transfer missing');count++}}}return {views:count,articles:DATA.articles.length}}''')
  await page.evaluate("openArticle('t2-46');setStep('read','task2')")
  await page.locator('#lesson2 .practice-review>summary').click()
  await page.locator('[data-review-drill] textarea').first.fill('batch saved answer')
  await page.reload();await page.wait_for_selector('#lesson2 .step-tabs',state='attached')
  assert await page.evaluate("USER.drafts['review:t2-46:nine:1']")=='batch saved answer'
  await page.evaluate("go('archive')");assert await page.evaluate("DATA.essays.filter(e=>e.title.includes('练习1·')).length")==9
  await page.evaluate("go('versions')");assert '1.9.0 → 1.10.0' in await page.locator('#diffResult').inner_text()
  await page.set_viewport_size({'width':390,'height':844})
  for i in range(43,52):
   await page.evaluate("id=>openArticle(id)",f't2-{i}')
   for step in ['read','cloze','translate','transfer']:
    await page.evaluate("s=>setStep(s,'task2')",step)
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(i,step)
  assert not errors,errors
  print(json.dumps(result));await browser.close()
asyncio.run(main())
