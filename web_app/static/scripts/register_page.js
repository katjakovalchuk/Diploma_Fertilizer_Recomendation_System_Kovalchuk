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

        const response = await fetch("/diploma/fertilizer_recommendation/register",
            {
                method: "POST",
                body: formData
            }
        );

        if (response.ok) {
            window.location.href = "/diploma/fertilizer_recommendation/login"
        }
    })
}

