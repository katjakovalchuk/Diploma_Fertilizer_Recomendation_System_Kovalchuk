const search_button = document.getElementById("search_button")
const add_field_button = document.getElementById("add_field_button")

if (search_button) {
    search_button.addEventListener('click', function () {
        console.log("Searching for your fields...")
    })
}

if (add_field_button) {
    add_field_button.addEventListener('click', function () {
        window.location.href = "/diploma/fertilizer_recommendation/field_creation"
    })
}

