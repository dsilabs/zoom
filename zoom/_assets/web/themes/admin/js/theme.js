// theme.js ---------------------------

document.addEventListener('keydown', function(event) {
  // Check if both the 'Ctrl' key and the 'Enter' key are pressed
  if (event.ctrlKey && event.key === 'Enter') {
      // Look for "save-button" first, then "create-button"
      let saveButton = document.querySelector('#save_button');
      let createButton = document.querySelector('#create_button');

      if (saveButton) {
          saveButton.click();
      } else if (createButton) {
          createButton.click();
      }
  }
});

// theme.js end -----------------------