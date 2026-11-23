import asyncio,json,os,shutil,subprocess
from pathlib import Path
from playwright.async_api import async_playwright
r=Path(__file__).resolve().parents[1]
data=json.loads((r/'data/connector-library.json').read_text())
old=json.loads(subprocess.check_output(['git','show','64bd0c6:data/connector-library.json'],cwd=r))
assert all(data[k]==v for k,v in old.items() if k!='topics')
assert len(data['topics'])==11 and sum(len(t['positive'])+len(t['negative']) for t in data['topics'])==68
assert all((r/f'data/articles/{a["id"]}.json').exists() for t in data['topics'] for a in t['related'])
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path=shutil.which('chromium'))
  page=await b.new_page(ignore_https_errors=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.add_init_script("localStorage.setItem('ielts-gate','1')")
  await page.goto(os.getenv('IELTS_TEST_URL','http://127.0.0.1:8023'));await page.wait_for_selector('#lesson2 .step-tabs',state='attached')
  await page.evaluate("go('connectors');showConnectorTab('topics')")
  assert await page.locator('[data-topic-card]').count()==11
  assert await page.locator('[data-expression]').count()==68
  await page.get_by_role('button',name='显示全部例句',exact=True).click();assert await page.locator('.cx-example[open]').count()==68
  await page.get_by_role('button',name='隐藏全部例句',exact=True).click();assert await page.locator('.cx-example[open]').count()==0
  await page.locator('#cxSearch').fill('定语从句');assert await page.locator('[data-expression]:not(.cx-filter-hidden)').count()>0
  await page.locator('#cxSearch').fill('');await page.locator('#cx-topics .actions button').filter(has_text='大学是否').first.click()
  assert await page.evaluate('state.task2')=='t2-02'
  await page.set_viewport_size({'width':390,'height':844});await page.evaluate("go('connectors');showConnectorTab('topics');toggleTopicExamples(true)")
  assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert not errors,errors
  print('PASS: 11 topics / 68 expressions, search, examples, related article, mobile; other library sections unchanged')
  await b.close()
asyncio.run(main())
