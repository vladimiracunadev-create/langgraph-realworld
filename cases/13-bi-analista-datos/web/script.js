const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const messagesDiv = document.getElementById('messages');
const sqlSpan = document.querySelector('#step-sql span');
const execSpan = document.querySelector('#step-exec span');

async function askQuestion() {
    const question = userInput.value.trim();
    if (!question) return;

    // UI Updates
    addMessage(question, 'user');
    userInput.value = '';
    sqlSpan.textContent = 'Generando...';
    execSpan.textContent = 'Esperando...';

    const systemMsg = addMessage('Analizando...', 'system');

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.replace('data: ', '').trim();
                    if (dataStr === '[DONE]') continue;

                    try {
                        const status = JSON.parse(dataStr);
                        updateUI(status, systemMsg);
                    } catch (e) {
                         // Partials
                    }
                }
            }
        }
    } catch (error) {
        systemMsg.textContent = 'Lo siento, ocurrió un error al procesar tu solicitud.';
        console.error(error);
    }
}

let businessChart = null;

function renderChart(data) {
    const ctx = document.getElementById('businessChart').getContext('2d');
    
    if (businessChart) {
        businessChart.destroy();
    }

    if (!data || !data.labels || data.labels.length === 0) {
        document.getElementById('viz-container').style.display = 'none';
        return;
    }

    document.getElementById('viz-container').style.display = 'flex';

    businessChart = new Chart(ctx, {
        type: data.labels.length > 5 ? 'bar' : 'pie',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: data.labels.length <= 5,
                    labels: { color: '#f8fafc' }
                }
            },
            scales: data.labels.length > 5 ? {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            } : {}
        }
    });
}

function updateUI(status, messageEl) {
    if (status.sql_query) {
        sqlSpan.textContent = status.sql_query;
    }
    if (status.execution_results) {
        execSpan.textContent = status.execution_results;
    }
    if (status.chart_data) {
        renderChart(status.chart_data);
    }
    if (status.final_answer) {
        messageEl.innerHTML = status.final_answer;
    }
}

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = text;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}

sendBtn.addEventListener('click', askQuestion);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') askQuestion();
});

function fillInput(text) {
    userInput.value = text;
    askQuestion();
}
