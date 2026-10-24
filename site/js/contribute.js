/* The prompt and launch links also work without JavaScript. */
const prompt = document.getElementById('agent-prompt');
const status = document.getElementById('copy-status');
for (const button of document.querySelectorAll('[data-copy-prompt]')) {
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
