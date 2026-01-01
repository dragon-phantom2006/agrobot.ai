async function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value;
    if (!message) return;

    const messagesDiv = document.getElementById("messages");
    messagesDiv.innerHTML += `<p><b>You:</b> ${message}</p>`;

    input.value = "";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        if (data.reply) {
            messagesDiv.innerHTML += `<p><b>AGROBOT:</b> ${data.reply}</p>`;
        } else {
            messagesDiv.innerHTML += `<p style="color:red;">Server error</p>`;
        }

    } catch (error) {
        messagesDiv.innerHTML += `<p style="color:red;">Backend not running</p>`;
    }
}
