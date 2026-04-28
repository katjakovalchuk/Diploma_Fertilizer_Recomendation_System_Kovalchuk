function showToast(message, type = 'error') {
    const colors = { error: '#c0392b', success: '#27ae60', warning: '#d4a017' };
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px;
        background: ${colors[type] || colors.error};
        color: white; padding: 12px 20px; border-radius: 8px;
        font-family: 'Alice', Georgia, serif; font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

const submit_log_in = document.getElementById("submit_log_in")

if (submit_log_in) {
    submit_log_in.addEventListener('click', async function () {
        let gmail = document.getElementById("gmail")
        let password = document.getElementById("password")

        const formData = new FormData()
        formData.append("gmail", gmail.value)
        formData.append("password", password.value)

        try {
            const response = await fetch("/diploma/fertilizer_recommendation/login", {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                window.location.href = "/diploma/fertilizer_recommendation/your_fields_page";
                return;
            }

            if (response.status === 401) {
                showToast("Wrong email or password");
            }

        } catch {
            showToast("No server connection");
        }
    });
}
