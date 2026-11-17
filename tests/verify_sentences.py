"""Check sentence training interactions and persistence against a local HTTP server."""
import asyncio,json,os,shutil,tempfile
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None)
  page=await browser.new_page(viewport={'width':1440,'height':1050})
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('dialog',lambda d:d.accept())
  await page.add_init_script("localStorage.setItem('ielts-gate','1')")
  await page.goto(os.environ.get('IELTS_TEST_URL','http://127.0.0.1:8000'))
  await page.wait_for_selector('#sentenceCatalog button',state='attached')
  await page.locator('.nav button[data-page=sentences]').click()
  assert await page.locator('#sentences').is_visible()
  assert await page.locator('#sentenceCatalog button').count()==8
  await page.locator('#sentenceCaseStudy > details > summary').click()
  assert await page.locator('#sentenceCaseStudy .sentence-example').count()==4
  case=await page.locator('#sentenceCaseStudy').inner_text()
  assert 'by which' in case and 'to which' in case and 'where' in case
  case_sentences=' '.join(await page.locator('#sentenceCaseStudy .sentence-example > p.en').all_text_contents())
  assert 'packeged' not in case_sentences and 'waterrr' not in case_sentences
  await page.locator('#sentenceCaseStudy > details > summary').click()
  results=await page.evaluate('''() => {
   let lessons=0, exercises=0;
   for(const l of DATA.sentenceTraining.lessons){
    selectSentenceLesson(l.id);lessons++;
    if(document.querySelectorAll('#sentenceContent .sentence-example').length!==l.examples.length)throw Error('Missing example');
    if(document.querySelectorAll('#sentenceContent .sentence-table tbody tr').length!==l.rules.length)throw Error('Missing rule');
    const label=document.querySelector('#sentenceCatalog button.active');if(!label||label.getAttribute('aria-pressed')!=='true')throw Error('Missing selected state');
    setSentenceMode('practice');const cards=[...document.querySelectorAll('[data-sentence-exercise]')];
    if(cards.length!==l.exercises.length)throw Error('Missing exercises');
    cards.forEach((c,i)=>{
     if(c.querySelector('.translation-cn').textContent!==l.exercises[i].cn)throw Error('Wrong prompt');
     if(c.querySelector('.sentence-reference').open)throw Error('Premature answer reveal');
     if(c.querySelector('.sentence-reference .en').textContent!==l.exercises[i].answer)throw Error('Wrong answer');
    });exercises+=cards.length;
   }
   selectSentenceLesson('preposition-relative');return {lessons,exercises};
  }''')
  await page.locator('#sentenceLesson button',has_text='02 6题迁移训练').click()
  first=page.locator('[data-sentence-exercise]').first
  check=first.locator('input[type=checkbox]')
  await check.click();assert not await check.is_checked()
  assert '先写出' in await first.locator('[role=status]').inner_text()
  await first.locator('textarea').fill('The diagram illustrates the process by which recycled paper is produced.')
  answer=first.locator('.sentence-reference');assert not await answer.get_attribute('open')
  await answer.locator('summary').focus();await page.keyboard.press('Enter')
  assert await answer.evaluate('(el)=>el.open')
  await check.check()
  assert await page.locator('#sentenceLesson [data-sentence-progress]').inner_text()=='1'
  await first.locator('textarea').fill('Edited sentence by which I practise the structure.')
  assert not await check.is_checked()
  assert '重新' in await first.locator('[role=status]').inner_text()
  await check.check()
  # Lesson drafts and checkmarks must persist after switching and reload.
  await page.evaluate("selectSentenceLesson('relative-adverbs');setSentenceMode('practice')")
  await page.locator('[data-sentence-exercise] textarea').first.fill('The milk is delivered to a factory, where it is heated.')
  await page.reload();await page.wait_for_selector('#sentenceCatalog button',state='attached')
  await page.locator('.nav button[data-page=sentences]').click()
  assert '关系副词' in await page.locator('#sentenceLesson h2').inner_text()
  await page.evaluate("setSentenceMode('practice')")
  assert 'The milk is delivered' in await page.locator('[data-sentence-exercise] textarea').first.input_value()
  await page.evaluate("selectSentenceLesson('preposition-relative');setSentenceMode('practice')")
  assert await page.locator('[data-sentence-exercise] textarea').first.input_value()=='Edited sentence by which I practise the structure.'
  assert await page.locator('[data-sentence-exercise] input[type=checkbox]').first.is_checked()
  # Save a pre-existing essay draft, export all records, clear the sentence records and import them.
  await page.evaluate("USER.drafts['tr:t1-31:nine:3']='existing essay draft';saveUser()")
  async with page.expect_download() as dl:await page.evaluate('exportBackup()')
  with tempfile.TemporaryDirectory() as tmp:
   backup=Path(tmp)/'backup.json';await (await dl.value).save_as(backup)
   data=json.loads(backup.read_text());assert data['user']['completed']['sentence:preposition-relative:1']
   assert data['user']['drafts']['tr:t1-31:nine:3']=='existing essay draft'
   await page.evaluate("for(const k of Object.keys(USER.drafts)){if(k.startsWith('sentence:'))delete USER.drafts[k]}for(const k of Object.keys(USER.completed)){if(k.startsWith('sentence:'))delete USER.completed[k]}saveUser();renderSentenceTraining()")
   await page.locator('#importBackup').set_input_files(backup)
   await page.wait_for_function("document.querySelector('[data-sentence-draft=\"sentence:preposition-relative:1\"]').value.startsWith('Edited sentence')")
   assert await page.locator('[data-sentence-exercise] input[type=checkbox]').first.is_checked()
  # Inspect desktop and mobile layouts; tables scroll in their own container.
  await page.evaluate("selectSentenceLesson('preposition-relative')")
  await page.screenshot(path='/workspace/work/sentences-desktop.png',full_page=True)
  await page.set_viewport_size({'width':390,'height':844})
  assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Mobile page overflow'
  await page.screenshot(path='/workspace/work/sentences-mobile.png',full_page=True)
  await page.evaluate("setSentenceMode('practice')")
  assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Mobile exercise overflow'
  assert not errors,errors
  print(json.dumps({**results,'answer_reveal':'passed','empty_check_guard':'passed','draft_and_progress_persistence':'passed','edits_invalidate_checks':'passed','backup_restore':'passed','mobile_layout':'passed','page_errors':errors}))
  await browser.close()

asyncio.run(main())
