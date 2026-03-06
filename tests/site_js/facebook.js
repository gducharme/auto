function clickExactInteractiveElementByText(text, index) {
  const SELECTOR = '[role="button"], button, a, div, span';

  // Gather candidates
  const all = Array.from(document.querySelectorAll(SELECTOR));
  const candidates = all.filter(
    (e) =>
      (e.textContent?.trim?.() || "") === text ||
      e.getAttribute?.("aria-label") === text
  );

  console.group(`debugClick: searching for '${text}'`);
  console.log('Total clickable elements on page:', all.length);
  console.log('Matching candidates count:', candidates.length);

  candidates.forEach((el, idx) => {
    const rect = el.getBoundingClientRect();
    const inViewport =
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth);

    console.group(`Candidate ${idx}`);
    console.log('Element:', el);
    console.log('Text:', el.textContent.trim());
    console.log('Aria-label:', el.getAttribute('aria-label'));
    console.log('Role:', el.getAttribute('role'));
    console.log('Tabindex:', el.getAttribute('tabindex'));
    console.log('Bounding rect:', rect);
    console.log('Visible (in viewport):', inViewport);
    console.groupEnd();
  });

  if (candidates.length === 0) {
    console.warn(`No element found with text or aria-label '${text}'.`);
    console.groupEnd();
    return null;
  }

  // If multiple matches and no index provided -> error out
  if (candidates.length > 1 && (index === undefined || index === null)) {
    const range = `0..${candidates.length - 1}`;
    console.error(
      `Ambiguous match: found ${candidates.length} elements for '${text}'. ` +
      `Provide an index (${range}) as the second argument.`
    );
    console.groupEnd();
    throw new Error(
      `Ambiguous match for '${text}'. Multiple elements found and no index provided.`
    );
  }

  // Resolve/validate index
  const i = index == null ? 0 : Number(index);
  if (!Number.isInteger(i) || i < 0 || i >= candidates.length) {
    const range = `0..${candidates.length - 1}`;
    console.error(`Index ${index} out of range. Valid indices: ${range}.`);
    console.groupEnd();
    throw new Error(`Index out of range for '${text}': ${index}`);
  }

  // Click the selected element
  const el = candidates[i];
  try {
    el.scrollIntoView?.({ block: 'center', inline: 'center' });
    el.focus?.();
    // Prefer native click; fall back to dispatch if needed
    if (typeof el.click === 'function') {
      el.click();
    } else {
      el.dispatchEvent(
        new MouseEvent('click', { bubbles: true, cancelable: true, view: window })
      );
    }
    console.log(`Clicked candidate index ${i}.`, el);
  } catch (err) {
    console.error('Failed to click element:', err);
    console.groupEnd();
    throw err;
  }

  console.groupEnd();
  return el;
}

function clickExactInteractiveElementByTextFirst(text) {
  return clickExactInteractiveElementByText(text, 0);
}

// Backward-compatible aliases for older fixtures.
function debugClickElementByText(text, index) {
  return clickExactInteractiveElementByText(text, index);
}

function clickElementByText(text) {
  return clickExactInteractiveElementByTextFirst(text);
}


function simulatePaste(text) {
  const editable = document.querySelector('[contenteditable="true"][role="textbox"]');

  if (!editable) {
    console.error("❌ No editable element found.");
    return;
  }

  editable.focus();

  const data = new DataTransfer();
  data.setData('text/plain', text);

  const pasteEvent = new ClipboardEvent('paste', {
    clipboardData: data,
    bubbles: true,
    cancelable: true
  });

  const result = editable.dispatchEvent(pasteEvent);
  console.log(`📋 Paste event dispatched: ${result ? "success" : "failure"}`);
}
