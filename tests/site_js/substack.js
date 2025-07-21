function clickButtonByText(text) {
  const button = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent.trim() === text);

  if (!button) {
    console.warn(`No button found with text '${text}'`);
    return;
  }

  // Focus the button
  button.focus();

  // Simulate full pointer & mouse event sequence
  ['pointerover', 'pointerenter', 'pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click', 'pointerout', 'pointerleave']
    .forEach(type => {
      const event = new MouseEvent(type, {
        view: window,
        bubbles: true,
        cancelable: true,
      });
      button.dispatchEvent(event);
    });

  console.log(`Simulated user click sequence on button with text '${text}'`);
}
