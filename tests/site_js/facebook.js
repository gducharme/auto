// Enhanced diagnostic click function with prioritized selection
function debugClickElementByText(text) {
  // Gather candidates
  const candidates = Array.from(
    document.querySelectorAll('[role="button"], button, a, div, span')
  ).filter(e => e.textContent.trim() === text || e.getAttribute('aria-label') === text);

  console.group(`debugClick: searching for '${text}'`);
  console.log('Total clickable elements on page:', document.querySelectorAll('[role="button"], button, a, div, span').length);
  console.log('Matching candidates count:', candidates.length);

  candidates.forEach((el, idx) => {
    const rect = el.getBoundingClientRect();
    console.group(`Candidate ${idx}`);
    console.log('Element:', el);
    console.log('Text:', el.textContent.trim());
    console.log('Aria-label:', el.getAttribute('aria-label'));
    console.log('Role:', el.getAttribute('role'));
    console.log('Tabindex:', el.getAttribute('tabindex'));
    console.log('Bounding rect:', rect);
    console.log('Visible (in viewport):', rect.top >= 0 && rect.left >= 0 && rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && rect.right <= (window.innerWidth || document.documentElement.clientWidth));
    console.groupEnd();
  });

  if (candidates.length === 0) {
    console.warn(`No element found with text or aria-label '${text}'.`);
    console.groupEnd();
    return;
  }

  // Prioritize element with aria-label or role="button"
  const el = candidates.find(e => e.getAttribute('aria-label') === text || e.getAttribute('role') === 'button') || candidates[0];
  console.log('Selected element for click:', el);

  // Simulate full pointer & mouse event sequence
  ['pointerover','pointerenter','pointerdown','mousedown','pointerup','mouseup','click','pointerout','pointerleave']
    .forEach(type => {
      const event = new MouseEvent(type, { view: window, bubbles: true, cancelable: true });
      console.log(`Dispatching event: ${type}`);
      el.dispatchEvent(event);
    });

  console.log(`Completed event dispatch sequence on element with text/aria-label '${text}'`);
  console.groupEnd();
}
