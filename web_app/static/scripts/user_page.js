const return_button = document.getElementById("return_nutton")

if (return_button) {
    return_button.addEventListener('click', async function () {
        window.location.href = "/diploma/fertilizer_recommendation/your_fields_page"
    })
}
