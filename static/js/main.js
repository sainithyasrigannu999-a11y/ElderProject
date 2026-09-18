document.addEventListener('DOMContentLoaded', () => {
  const roleSelect = document.getElementById('roleSelect');
  if (roleSelect) {
    const updateRoleFields = () => {
      const show = roleSelect.value === 'elderly';
      document.querySelectorAll('.elder-fields').forEach((field) => {
        field.style.display = show ? 'block' : 'none';
      });
    };
    roleSelect.addEventListener('change', updateRoleFields);
    updateRoleFields();
  }
});
