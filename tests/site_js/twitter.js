/**
 * Removes all but the first <span data-text="true"> on the page,
 * then sets that remaining span’s text content to the given text.
 *
 * @param {string} newText — the text to set on the remaining span
 */
function collapseSpansToText(newText) {
  // Grab all spans with data-text="true"
  const spans = Array.from(document.querySelectorAll('span[data-text="true"]'));

  if (spans.length === 0) {
    console.warn('No <span data-text="true"> elements found.');
    return;
  }

  // Keep the first span, remove the rest
  const [firstSpan, ...others] = spans;
  others.forEach(span => span.remove());

  // Update the remaining span
  firstSpan.textContent = newText;

  console.log(
    `Kept 1 span and updated its text to "${newText}" ` +
    `(removed ${others.length} span${others.length === 1 ? '' : 's'}).`
  );
}
