/* The prompt and launch links also work without JavaScript. */
for (const button of document.querySelectorAll('[data-copy-prompt]')) {
  const prompt = document.getElementById(button.dataset.copyPrompt);
  const status = document.getElementById(button.dataset.copyStatus);
  button.hidden = false;
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(prompt.value);
      status.textContent = 'Prompt copied.';
    } catch {
      prompt.focus();
      prompt.select();
      status.textContent = 'Select and copy the highlighted prompt.';
    }
  });
}
