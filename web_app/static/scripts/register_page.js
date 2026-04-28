function showToast(message, type = 'error') {
    const colors = { error: '#c0392b', success: '#27ae60', warning: '#d4a017' };
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

const submit_sign_up = document.getElementById("submit_sign_up")

if (submit_sign_up) {
    submit_sign_up.addEventListener('click', async function () {
        let name = document.getElementById("name")
        let surname = document.getElementById("surname")
        let region = document.getElementById("region")
        let gmail = document.getElementById("gmail")
        let password = document.getElementById("password")
        let repeat_password = document.getElementById("repeat-password")

        const formData = new FormData()
        formData.append("name", name.value)
        formData.append("surname", surname.value)
        formData.append("region", region.value)
        formData.append("gmail", gmail.value)
        formData.append("password", password.value)
        formData.append("repeat_password", repeat_password.value)

        try {
            const response = await fetch("/diploma/fertilizer_recommendation/register", {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                showToast("Register successful!", "success");
                setTimeout(() => {
                    window.location.href = "/diploma/fertilizer_recommendation/login";
                }, 1500);
                return;
            }

            const data = await response.json().catch(() => ({}));

            if (response.status === 409) {
                showToast("Someone already registered this email");
            }

        } catch {
            showToast("No server connection");
        }
    })
}

