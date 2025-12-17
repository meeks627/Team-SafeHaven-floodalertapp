document.getElementById('floodForm').addEventListener('submit', async function(e){
    e.preventDefault();

    const formData = Object.fromEntries(new FormData(this).entries());

    // Only convert numeric inputs to float
    const numericFields = ['rain_24h','rain_72h','rhum','drainage_score','elevation_score'];
    for (let key of numericFields) {
        formData[key] = parseFloat(formData[key]);
    }

    // Leave phone_numbers as string
    formData['phone_numbers'] = formData['phone_numbers'].trim();

    // Send data to Flask
    const response = await fetch('/predict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    });

    const data = await response.json();

    // Display alert
    const resultDiv = document.getElementById('result');
    resultDiv.innerText = data.alert;

    // Optional: color-code result
    if (data.alert.includes("HIGH RISK")) {
        resultDiv.style.backgroundColor = "#ff4d4d"; // red
        resultDiv.style.color = "#fff";
    } else if (data.alert.includes("MODERATE RISK")) {
        resultDiv.style.backgroundColor = "#ffd11a"; // yellow
        resultDiv.style.color = "#000";
    } else {
        resultDiv.style.backgroundColor = "#66cc66"; // green
        resultDiv.style.color = "#fff";
    }
});
