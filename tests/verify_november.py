import asyncio,os,shutil
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path=shutil.which('chromium'))
  page=await b.new_page(ignore_https_errors=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.add_init_script("localStorage.setItem('ielts-gate','1')")
  await page.goto(os.getenv('IELTS_TEST_URL','http://127.0.0.1:8024'));await page.wait_for_selector('#lesson2 .step-tabs',state='attached')
  await page.get_by_role('button',name='11月考频预测整理',exact=True).click()
  assert await page.locator('#november').is_visible()
  text=await page.locator('#november').inner_text()
  for term in ['父母 vs 外界','强制所有父母','陪产假','太空探索','机票降价','自产全部食物','免费图书馆','本地历史','示例 A','示例 B','四个非洲国家','11月28日','[A]%','未独立核验']:
   assert term in text,term
  assert '下载完整' not in text and await page.locator('#november img').count()==0
  assert await page.locator('#november table').count()==4
  for width in [1440,390]:
   await page.set_viewport_size({'width':width,'height':900})
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  await page.evaluate("openArticle('t2-51')");assert await page.locator('#lesson2 .modelp').count()==4
  assert not errors,errors
  print('PASS independent November module; all sections, placeholders, desktop/mobile and article navigation')
  await b.close()
asyncio.run(main())
