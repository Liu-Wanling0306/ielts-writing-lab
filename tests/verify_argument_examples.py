import asyncio,json,os,shutil,re,subprocess
from pathlib import Path
from playwright.async_api import async_playwright
r=Path(__file__).resolve().parents[1];data=json.loads((r/'data/november-argument-examples.json').read_text());rows=data['examples'];assert len(rows)==40 and len({x['id'] for x in rows})==40
old=subprocess.check_output(['git','show','11182c7:data/november-sprint.md'],cwd=r,text=True);old=old[old.index('## **二、'):old.index('## **三、')];sentences=re.findall(r'^> (.+)$',old,re.M)
assert len(sentences)==14 and set(sentences)=={x['example'] for x in rows if x['existing']}
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path=shutil.which('chromium'));page=await b.new_page(ignore_https_errors=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.add_init_script("localStorage.setItem('ielts-gate','1')")
  await page.goto(os.getenv('IELTS_TEST_URL','http://127.0.0.1:8040'));await page.wait_for_selector('#lesson2 .step-tabs',state='attached');await page.evaluate("go('november')")
  assert await page.locator('#nov-section-2 [data-argument-example]').count()==28
  assert await page.locator('#nov-section-3 [data-argument-example]').count()==12
  assert await page.evaluate('''()=>[...document.querySelectorAll('#nov-section-2 .nov-bullet')].every(p=>p.nextElementSibling?.matches('blockquote[data-argument-example]'))''')
  text=await page.locator('#november').inner_text()
  for row in rows:assert row['example'] in text,row['id']
  await page.set_viewport_size({'width':390,'height':844});assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert not errors,errors
  print('PASS 28 core + 12 extension argument/example pairs; original14 preserved; adjacent placement and mobile')
  await b.close()
asyncio.run(main())
