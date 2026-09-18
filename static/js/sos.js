document.addEventListener('DOMContentLoaded', () => {
  const sosButton = document.getElementById('sosButton');
  if (!sosButton) return;

  sosButton.addEventListener('click', () => {
    const modal = new bootstrap.Modal(document.getElementById('sosModal'));
    modal.show();
  });

  document.getElementById('confirmSosBtn')?.addEventListener('click', async () => {
    const formData = new FormData();
    formData.append('description', 'I need emergency help.');
    formData.append('input_type', 'sos');
    formData.append('location_text', 'Manual location');

    const response = await fetch('/elderly/dashboard/sos', { method: 'POST', body: formData });
    const data = await response.json();
    const alertBox = document.getElementById('alertArea');
    if (alertBox) {
      alertBox.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
    }

    const modal = bootstrap.Modal.getInstance(document.getElementById('sosModal'));
    modal.hide();
    showConfirmationModal(data.emergency_id, 'I need emergency help.');
  });

  function showConfirmationModal(emergencyId, description) {
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    const confirmationText = document.getElementById('confirmationText');
    confirmationText.textContent = `We have recorded your emergency. Are you okay?`;

    let timerId = setTimeout(async () => {
      const payload = new FormData();
      payload.append('choice', 'timeout');
      payload.append('emergency_id', emergencyId);
      payload.append('description', description);
      const response = await fetch('/elderly/dashboard/confirm', {
        method: 'POST',
        body: payload,
      });
      const data = await response.json();
      const alertBox = document.getElementById('alertArea');
      if (alertBox) {
        alertBox.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
      }
      modal.hide();
    }, Number(window.confirmationTimeoutSeconds || 30) * 1000);

    document.querySelectorAll('[data-confirm]').forEach((button) => {
      button.onclick = async () => {
        clearTimeout(timerId);
        const choice = button.getAttribute('data-confirm');
        const payload = new FormData();
        payload.append('choice', choice);
        payload.append('emergency_id', emergencyId);
        payload.append('description', description);

        const response = await fetch('/elderly/dashboard/confirm', {
          method: 'POST',
          body: payload,
        });
        const data = await response.json();
        const alertBox = document.getElementById('alertArea');
        if (alertBox) {
          alertBox.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
        }
        modal.hide();
      };
    });

    modal.show();
  }
});
