function clickMediumWrite() {
  console.log('🔍 Looking for Medium “Write” button…');
  // first try the <a data-testid="headerWriteButton">
  let btn = document.querySelector('a[data-testid="headerWriteButton"]');

  // if that fails, fall back to any div with textContent “Write”
  if (!btn) {
    btn = Array.from(document.querySelectorAll('div.ao.y'))
      .find(el => el.textContent.trim() === 'Write')
      ?.closest('a');
  }

  if (btn) {
    console.log('✅ Found it:', btn);
    btn.click();
    console.log('👉 Click dispatched.');
  } else {
    console.warn('❌ Couldn’t find the “Write” button.');
  }
}
