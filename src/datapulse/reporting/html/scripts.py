# =========================================================================
# DataPulse HTML Report Client Scripts
# Lightweight Vanilla JavaScript for instant real-time column search.
# =========================================================================

HTML_SCRIPT = """
const sBox = document.getElementById('column-search');
sBox?.addEventListener('input', function(e) {
    const query = e.target.value.toLowerCase().trim();
    const rows = document.querySelectorAll('.col-row');
    rows.forEach(row => {
        const name = row.getAttribute('data-name') || '';
        const role = row.getAttribute('data-role') || '';
        if (name.includes(query) || role.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});
"""
