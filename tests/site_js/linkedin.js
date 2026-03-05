function clickPrimaryButtonByText(label) {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.querySelector('.artdeco-button__text')?.textContent.trim() === label);
  if (!btn) return console.warn(`No primary button found with label '${label}'`);
  btn.click(); console.log(`Clicked primary button '${label}'`);
}

function typeTextInEditor(text) {
  const editor = document.querySelector('.ql-editor');
  if (!editor) throw new Error("No .ql-editor found");

  editor.focus();

  // Build up paragraphs for each line
  const html = text
    .split('\n')
    .map(line => `<p>${line || '<br>'}</p>`)
    .join('');

  // Insert HTML at the caret
  document.execCommand('insertHTML', false, html);

  // Notify Quill (or any listener) that we changed the content
  editor.dispatchEvent(new InputEvent('input', { bubbles: true }));
}

// Usage:
// typeTextInEditor(`Hello world!
// This is a new paragraph.
// #withHashtag and <strong>formatting</strong>`);
