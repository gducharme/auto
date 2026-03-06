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

function fillCaption(text) {
  console.log('🔍 Looking for caption editor…');
  const editable = Array.from(
    document.querySelectorAll('div[contenteditable="true"], textarea')
  ).find(e => {
    const label = (e.getAttribute('aria-label') || '').toLowerCase();
    return (
      e.tagName === 'TEXTAREA' ||
      label.includes('caption') ||
      label.includes('write a caption')
    );
  });
  if (!editable) {
    console.warn('❌ No caption editor found.');
    return false;
  }

  if (editable.tagName === 'TEXTAREA') {
    editable.focus();
    editable.value = text;
    editable.dispatchEvent(new Event('input', { bubbles: true }));
    editable.dispatchEvent(new Event('change', { bubbles: true }));
    console.log('🚀 Filled textarea caption.');
    return true;
  }

  editable.focus();
  editable.textContent = text;
  editable.dispatchEvent(new InputEvent('input', { bubbles: true, data: text }));
  console.log('🚀 Filled contenteditable caption.');
  return true;
}
