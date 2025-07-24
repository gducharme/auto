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

function clickShareButton() {
  // Select all candidate <a role="button"> elements with the right aria-label
  const candidates = document.querySelectorAll(
    'a[role="button"][aria-label="View share options"]'
  );

  for (const btn of candidates) {
    // Verify it really is the “Share” button by checking its label text
    const label = btn.querySelector('.label');
    if (label && label.textContent.trim() === 'Share') {
      btn.click();
      return console.log('Share button clicked.');
    }
  }

  console.warn('Share button not found');
}

/**
 * Finds and clicks the “Share to {platform}” button.
 *
 * @param {string} platformName — the name of the platform, e.g. "X", "Facebook", "Notes"
 */
function clickShareTo(platformName) {
  // Select all <button> elements on the page
  const buttons = document.querySelectorAll('button[type="button"]');

  for (const btn of buttons) {
    // Most of these buttons have two child <div>s:
    //   0: icon container
    //   1: label container
    const labelDiv = btn.children[1];
    if (!labelDiv) continue;

    // Does its text match exactly "Share to {platformName}"?
    if (labelDiv.textContent.trim() === `Share to ${platformName}`) {
      btn.click();
      console.log(`Clicked "Share to ${platformName}" button.`);
      return;
    }
  }

  console.warn(`No "Share to ${platformName}" button found.`);
}
