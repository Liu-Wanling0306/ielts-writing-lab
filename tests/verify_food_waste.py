"""Verify both food-waste editions, complete training, persistent drills and stable error IDs."""
import asyncio,json,os,shutil,tempfile
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None)
  page=await browser.new_page(viewport={'width':1440,'height':1050},ignore_https_errors=True);errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
  await page.add_init_script("localStorage.setItem('ielts-gate','1')")
  await page.goto(os.environ.get('IELTS_TEST_URL','http://127.0.0.1:8020'));await page.wait_for_selector('#lesson2 .step-tabs',state='attached')
  await page.get_by_role('button',name='打开食物浪费双版本训练').click()
  assert await page.locator('#task2').is_visible() and await page.evaluate('state.task2')=='t2-42'
  assert '保留原意' in await page.locator('#lesson2').inner_text() and '7.5' in await page.locator('#lesson2').inner_text()
  result=await page.evaluate('''()=>{const a=DATA.articles.find(a=>a.id==='t2-42');const result={};for(const version of ['seven','nine']){setEdition(a,version,'task2');const ps=paras(a);for(const step of ['read','cloze','translate','transfer']){setStep(step,'task2');const target=document.querySelector('#lesson2 #stepContent');const count=target.querySelectorAll(step==='read'?'.modelp':step==='transfer'?'[data-transfer-item]':'.clozebox').length;if(count!==(step==='transfer'?a.transfer[version].length:4))throw Error('Missing content '+version+'/'+step);if(step==='cloze'){target.querySelectorAll('.blankinput').forEach(n=>{if(!n.dataset.answer)throw Error('Missing answer')})}if(step==='translate')target.querySelectorAll('.translation-cn').forEach((n,i)=>{if(n.textContent!==ps[i].cn)throw Error('Incomplete translation')})}result[version]={paragraphs:ps.length,transfer:a.transfer[version].length}}return result}''')
  await page.evaluate("setEdition(DATA.articles.find(a=>a.id==='t2-42'),'seven','task2')")
  await page.locator('#lesson2 .practice-review>summary').click();assert await page.locator('[data-review-drill]').count()==5
  assert '冠词' in await page.locator('#lesson2 .practice-review').inner_text()
  field=page.locator('[data-review-drill] textarea').first;await field.fill('saved version A drill')
  await page.evaluate("setEdition(DATA.articles.find(a=>a.id==='t2-42'),'nine','task2')")
  await page.locator('#lesson2 .practice-review>summary').click();assert await page.locator('[data-review-drill] textarea').first.input_value()==''
  await page.locator('[data-review-drill] textarea').first.fill('saved version B drill')
  await page.reload();await page.wait_for_selector('#lesson2 .step-tabs',state='attached');await page.evaluate("openArticle('t2-42');setEdition(DATA.articles.find(a=>a.id==='t2-42'),'seven','task2')")
  await page.locator('#lesson2 .practice-review>summary').click();assert await page.locator('[data-review-drill] textarea').first.input_value()=='saved version A drill'
  await page.evaluate("USER.extraErrors.push(['legacy personal error','legacy corrected','old explanation','']);USER.answers['err:'+DATA.errors.length]='old personal answer';USER.review[DATA.errors.length]=true;USER.completed['error:'+DATA.errors.length]=true;saveUser();go('errors')")
  old_count=await page.evaluate('DATA.errors.length');old=page.locator(f'[data-error-item="{old_count}"]');assert 'legacy personal error' in await old.inner_text();assert await old.locator('input').input_value()=='old personal answer'
  assert await page.locator('[data-error-item^="t2-42:"]').count()==13
  article_error=page.locator('[data-error-item="t2-42:e01"]');expected=await page.evaluate("errorEntries().find(x=>x.id==='t2-42:e01').e[1]")
  await article_error.locator('input').fill(expected);await article_error.get_by_role('button',name='核对',exact=True).click();assert '一致' in await article_error.locator('.feedback').inner_text()
  await article_error.get_by_role('button',name='标记待复习').click()
  await page.locator('#newWrong').fill('another custom error');await page.locator('#newCorrect').fill('another corrected');await page.locator('#newExplain').fill('custom note');await page.get_by_role('button',name='加入个人错题').click()
  assert await page.locator(f'[data-error-item="{old_count}"] input').input_value()=='old personal answer'
  assert await page.locator('[data-error-item="t2-42:e01"] input').input_value()==expected
  await page.evaluate("go('versions')");assert '1.8.0 → 1.9.0' in await page.locator('#diffResult').inner_text()
  async with page.expect_download() as downloaded:await page.evaluate('exportBackup()')
  with tempfile.TemporaryDirectory() as tmp:
   file=Path(tmp)/'backup.json';await (await downloaded.value).save_as(file);data=json.loads(file.read_text());assert data['user']['answers']['err:t2-42:e01']==expected
   await page.evaluate("localStorage.removeItem(keyName('user'))");await page.reload();await page.wait_for_selector('#lesson2 .step-tabs',state='attached');await page.locator('#importBackup').set_input_files(file)
   await page.wait_for_function("USER.answers['err:t2-42:e01']!==undefined");assert await page.evaluate("USER.drafts['review:t2-42:seven:1']")=='saved version A drill'
  await page.evaluate("go('archive')");assert 'R04 / T2-42' in await page.locator('#essayArchive').inner_text();assert await page.evaluate('DATA.essays.find(e=>e.title.includes("食物浪费")).feedback.includes("原稿")')
  await page.set_viewport_size({'width':390,'height':844});await page.evaluate("openArticle('t2-42')")
  for version in ['seven','nine']:
   await page.evaluate("v=>setEdition(DATA.articles.find(a=>a.id==='t2-42'),v,'task2')",version)
   for step in ['read','cloze','translate','transfer']:
    await page.evaluate("s=>setStep(s,'task2')",step);assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),version+'/'+step
  assert not errors,errors;await browser.close();print(json.dumps({**result,'drill_persistence':'passed','legacy_error_ids':'preserved','new_error_ids':'stable','backup_restore':'passed','mobile':'passed','page_errors':errors}))
asyncio.run(main())
