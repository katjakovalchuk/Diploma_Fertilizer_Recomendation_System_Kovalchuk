const submit_field_creation = document.getElementById("submit_field_creation")

if (submit_field_creation) {
    submit_field_creation.addEventListener('click', async function () {
        e.preventDefault()

        let field_name = document.getElementById("field_name")
        let area = document.getElementById("area")
        let farm = document.getElementById("farm")
        let crop = document.getElementById("crop")
        let ton = document.getElementById("ton")
        let fertilizer_type = document.getElementById("fertilizer_type")
        let file = document.getElementById("soil_analysis")

        const formData = new FormData()
        formData.append("field_name", field_name.value)
        formData.append("area", area.value)
        formData.append("farm", farm.value)
        formData.append("crop", crop.value)
        formData.append("ton", ton.value)
        formData.append("fertilizer_type", fertilizer_type.value)
        formData.append("soil_analysis", file.files[0])

        const response = await fetch("/diploma/fertilizer_recommendation/field_creation",
            {
                method: "POST",
                body: formData
            }
        );

        if (response.ok) {
            window.location.href = "/diploma/fertilizer_recommendation/recommendation"
        }
    })
}
