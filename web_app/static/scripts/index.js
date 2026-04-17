const log_in_button = document.getElementById("button_log_in")
const sign_up_button = document.getElementById("button_sign_up")

if (log_in_button) {
    log_in_button.addEventListener('click', () =>
        window.location.href = "/diploma/fertilizer_recommendation/login"
    )
}
    
if (sign_up_button) {
    sign_up_button.addEventListener('click', () =>
        window.location.href = "/diploma/fertilizer_recommendation/register"
    )
}