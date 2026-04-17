const submit_log_in = document.getElementById("submit_log_in")

if (submit_log_in) {
    submit_log_in.addEventListener('click', async function () {
        let gmail = document.getElementById("gmail")
        let password = document.getElementById("password")

        const formData = new FormData()
        formData.append("gmail", gmail.value)
        formData.append("password", password.value)

        const response = await fetch("/diploma/fertilizer_recommendation/login",
            {
                method: "POST",
                body: formData
            }
        );

        if (response.ok) {
            window.location.href = "/diploma/fertilizer_recommendation/your_fields_page"
        }
    })
}
