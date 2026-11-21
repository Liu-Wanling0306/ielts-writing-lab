"""Verify grammar package, embedding, independent records and backup round trip."""
import asyncio,json,os,re,shutil,tempfile
from pathlib import Path
from playwright.async_api import async_playwright
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'data/grammar-review.json').read_text())
assert data==json.loads(re.search(r'<script id="grammarData" type="application/json">(.*?)</script>',(root/'grammar-review.html').read_text(),re.S).group(1))
qs=[q for l in data['lessons'] for q in l['exercises']]
assert len(data['lessons'])==12 and all(len(l['exercises'])==9 for l in data['lessons'])
assert len(qs)==len({q['id'] for q in qs})==108
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path=shutil.which('chromium'))
  page=await b.new_page(ignore_https_errors=True,accept_downloads=True)
  await page.add_init_script("localStorage.setItem('ielts-gate','1')")
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
  await page.goto(os.getenv('IELTS_TEST_URL','http://127.0.0.1:8021'))
  await page.wait_for_selector('#lesson2 .step-tabs',state='attached')
  old=await page.evaluate("()=>{USER.drafts['grammar-regression']='keep old records';saveUser();return localStorage.getItem('ieltsLab:user')}")
  await page.evaluate("go('sentences')")
  assert await page.locator('#sentenceLesson').is_visible()
  assert await page.locator('#grammarReviewFrame').count()==0
  await page.locator('#grammarReviewTab').click()
  frame=page.frame_locator('#grammarReviewFrame');await frame.locator('.exercise').first.wait_for()
  for lesson in data['lessons']:
   await frame.locator(f'[data-lesson="{lesson["id"]}"]').click();assert await frame.locator('.exercise').count()==9
  lesson=data['lessons'][0];await frame.locator(f'[data-lesson="{lesson["id"]}"]').click()
  q=next(q for q in lesson['exercises'] if q['type']=='gap');card=frame.locator(f'[data-id="{q["id"]}"].exercise')
  await card.locator('input').fill('incorrect answer');await card.locator('[data-action="check"]').click()
  assert await card.locator('.answer.visible').count()==1
  assert '需复习' in await card.locator('.mark').first.inner_text()
  await frame.locator('#reviewBtn').click();assert await frame.locator(f'.exercise[data-id="{q["id"]}"]').count()==1
  await frame.locator(f'[data-lesson="{lesson["id"]}"]').click()
  assert await card.locator('input').input_value()=='incorrect answer'
  for answer in q['accepted']:
   await card.locator('input').fill(answer.upper());await card.locator('[data-action="check"]').click()
   assert '匹配' in await card.locator('.checking-status').inner_text()
  await card.locator('[data-action="review"]').click()
  store=json.loads(await page.evaluate("localStorage.getItem('ielts-grammar-review-v1.4')"));assert store[q['id']]['success']==0
  openq=next(q for q in lesson['exercises'] if q['type']=='translate');oc=frame.locator(f'.exercise[data-id="{openq["id"]}"]')
  await oc.locator('textarea').fill('A valid alternative may differ.');await oc.locator('[data-action="check"]').click()
  assert await oc.locator('.answer.visible').count()==1 and await oc.locator('.checking-status').count()==0
  await frame.locator('#progressBtn').click()
  async with page.expect_download() as event:await frame.locator('#exportBtn').click()
  with tempfile.TemporaryDirectory() as temp:
   f=Path(temp)/'progress.json';await (await event.value).save_as(f);backup=json.loads(f.read_text());assert backup['state'][q['id']]['draft']
   await page.evaluate("localStorage.removeItem('ielts-grammar-review-v1.4')")
   await page.locator('#grammarReviewFrame').evaluate('(f)=>f.contentWindow.location.reload()')
   await frame.locator('#progressBtn').click();await frame.locator('#importInput').set_input_files(f)
   await page.wait_for_function("JSON.parse(localStorage.getItem('ielts-grammar-review-v1.4')||'{}')["+json.dumps(q['id'])+"]?.answered")
  assert await page.evaluate("localStorage.getItem('ieltsLab:user')")==old
  await page.locator('#sentenceOriginalTab').click();assert await page.locator('#sentenceLesson').is_visible()
  for article in ['t1-31','t2-51']:
   await page.evaluate('id=>openArticle(id)',article);assert await page.locator('.page.active .modelp').count()==4
  await page.set_viewport_size({'width':390,'height':844});await page.evaluate("go('sentences');setSentencePanel('grammar')")
  assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert await page.locator('#grammarReviewFrame').evaluate('(f)=>f.contentDocument.documentElement.scrollWidth<=f.contentWindow.innerWidth')
  assert not errors,errors
  print('PASS: 12 lessons / 108 exercises; answers, review, drafts, JSON roundtrip, old records, Task1/2, mobile')
  await b.close()
asyncio.run(main())
