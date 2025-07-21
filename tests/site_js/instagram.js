function clickNext() {
  // Next is a div[role=button]
  console.log('🔍 Looking for Next div[role=button]…');
  const div = Array.from(document.querySelectorAll('div[role="button"]'))
    .find(e => e.textContent.trim() === 'Next');
  if (!div) {
    console.warn('❌ No Next button found.');
    return false;
  }
  console.log('✅ Found Next div:', div);
  div.click();
  console.log('🚀 Clicked Next!');
  return true;
}

function clickShare() {
  console.log('🔍 Looking for a Share button…');
  // look for <button> first
  let el = Array.from(document.querySelectorAll('button'))
    .find(e => e.textContent.trim() === 'Share');
  // fallback to div[role="button"]
  if (!el) {
    el = Array.from(document.querySelectorAll('div[role="button"]'))
      .find(e => e.textContent.trim() === 'Share');
  }
  if (!el) {
    console.warn('❌ No element with text "Share" found.');
    return false;
  }
  console.log('✅ Found Share element:', el);
  el.click();
  console.log('🚀 Clicked Share!');
  return true;
}
