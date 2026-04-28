const search_button = document.getElementById("search_button")
const add_field_button = document.getElementById("add_field_button")
const field_buttons = document.querySelectorAll(".one-field-button")

if (search_button) {
    search_button.addEventListener('click', function () {
        console.log("Searching for your fields...")
    })
}

if (add_field_button) {
    add_field_button.addEventListener('click', function () {
        const fieldName = this.dataset.fieldName
        window.location.href = `/diploma/fertilizer_recommendation/field_creation?field_name=${fieldName}`
    })
}

field_buttons.forEach(function (one_button) {
    one_button.addEventListener('click', function () {
        const fieldName = this.dataset.fieldName
        window.location.href = `/diploma/fertilizer_recommendation/field?field_name=${fieldName}`
    })
});
