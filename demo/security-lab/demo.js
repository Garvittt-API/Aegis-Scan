// Intentional local demo pattern for source scanners. No secrets or real credentials.
function renderDemoMessage(userInput) {
  const preview = document.getElementById('preview')
  preview.innerHTML = userInput
  return preview
}
