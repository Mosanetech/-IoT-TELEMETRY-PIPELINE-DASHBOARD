const ws = new WebSocket("ws://127.0.0.1:8080/live");

const temp = document.getElementById("temp");
const humidity = document.getElementById("humidity");
const soil = document.getElementById("soil");
const light = document.getElementById("light");

const ctx = document.getElementById('chart');

const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Temperature',
            data: []
        }]
    }
});

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    temp.innerText = data.temperature.toFixed(2) + " °C";
    humidity.innerText = data.humidity.toFixed(2) + " %";
    soil.innerText = data.soil_moisture.toFixed(2) + " %";
    light.innerText = data.light.toFixed(2) + " lux";

    chart.data.labels.push(new Date().toLocaleTimeString());
    chart.data.datasets[0].data.push(data.temperature);

    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update();
};