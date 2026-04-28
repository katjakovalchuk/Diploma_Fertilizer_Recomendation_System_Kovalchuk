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

const submit_field_creation = document.getElementById("submit_field_creation")

if (submit_field_creation) {
    submit_field_creation.addEventListener('click', async function (e) {
        e.preventDefault()

        let field_name = document.getElementById("field_name")
        let area = document.getElementById("area")
        let farm = document.getElementById("farm")
        let crop = document.getElementById("crop")
        let fertilizer_type = document.getElementById("fertilizer_type")
        let target_yield_field = document.getElementById("target_yield")
        let file = document.getElementById("soil_analysis")

        const formData = new FormData()
        formData.append("field_name", field_name.value)
        formData.append("area", area.value)
        formData.append("farm", farm.value)
        formData.append("crop", crop.value)
        formData.append("fertilizer_type", fertilizer_type.value)
        formData.append("target_yield_field", target_yield_field.value)
        formData.append("soil_analysis", file.files[0])

        if (!field_name.value.trim() || !area.value.trim() || !farm.value.trim() ||
            !crop.value.trim() || !target_yield_field.value.trim()) {
            showToast("Please, fill all fields");
            return;
        }

        const areaVal = parseFloat(area.value);
        if (isNaN(areaVal) || areaVal <= 0) {
            showToast("Area should be greater, than 0");
            return;
        }

        const yieldVal = parseFloat(target_yield_field.value);
        if (isNaN(yieldVal) || yieldVal <= 0) {
            showToast("Target Yield should be greater, than 0");
            return;
        }

        if (!file.files || file.files.length === 0) {
            showToast("Upload soil analysis file");
            return;
        }

        if (!file.files[0].name.toLowerCase().endsWith('.csv')) {
            showToast("Only CSV files allowed");
            return;
        }

        try {
            const response = await fetch("/diploma/fertilizer_recommendation/field_creation", {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                window.location.href = response.url;
                return;
            }

        } catch {
            showToast("No server connection");
        }
        const data = await response.json();
        showToast(data.error || "Submission failed");
        
    });
}