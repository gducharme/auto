function clickPrimaryButtonByText(label) {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.querySelector('.artdeco-button__text')?.textContent.trim() === label);
  if (!btn) return console.warn(`No primary button found with label '${label}'`);
  btn.click(); console.log(`Clicked primary button '${label}'`);
}
