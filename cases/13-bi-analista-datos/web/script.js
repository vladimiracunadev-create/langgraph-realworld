const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const messagesDiv = document.getElementById('messages');
const sqlSpan = document.querySelector('#step-sql span');
const execSpan = document.querySelector('#step-exec span');
const modeBadge = document.getElementById('mode-badge');
const suggestionsEl = document.getElementById('suggestions');

let businessChart = null;
let isLoading = false;

function setLoading(next) {
    isLoading = next;
    sendBtn.disabled = next;
    userInput.disabled = next;
    sendBtn.textContent = next ? 'Consultando...' : 'Consultar';
}

function setBadge(mode) {
    modeBadge.textContent = mode || 'DEMO';
    modeBadge.dataset.mode = (mode || 'DEMO').toLowerCase();
}

function resetSteps() {
    sqlSpan.textContent = 'Generando...';
    execSpan.textContent = 'Esperando...';
}

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = text;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}

function renderSuggestions(examples = []) {
    if (!examples.length) return;
    suggestionsEl.innerHTML = '';
    examples.slice(0, 5).forEach((example) => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'suggest-card';
        chip.textContent = example;
        chip.addEventListener('click', () => fillInput(example));
        suggestionsEl.appendChild(chip);
    });
}

function renderChart(data) {
    const container = document.getElementById('viz-container');
    const ctx = document.getElementById('businessChart').getContext('2d');

    if (businessChart) {
        businessChart.destroy();
    }

    if (!data || !Array.isArray(data.labels) || !data.labels.length) {
        container.classList.add('is-empty');
        return;
    }

    container.classList.remove('is-empty');
    businessChart = new Chart(ctx, {
        type: data.type || 'bar',
        data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#f8fafc' },
                },
            },
            scales: ['bar', 'line'].includes(data.type)
                ? {
                      y: {
                          beginAtZero: true,
                          grid: { color: 'rgba(255,255,255,0.08)' },
                          ticks: { color: '#cbd5e1' },
                      },
                      x: {
                          grid: { display: false },
                          ticks: { color: '#cbd5e1' },
                      },
                  }
                : {},
        },
    });
}

function updateUI(status, messageEl) {
    if (status.mode) setBadge(status.mode);
    if (status.sql_query) sqlSpan.textContent = status.sql_query;
    if (status.execution_results) execSpan.textContent = status.execution_results;
    if (status.chart_data) renderChart(status.chart_data);
    if (status.final_answer) messageEl.textContent = status.final_answer;
    if (status.error) messageEl.textContent = `No pude completar la consulta. ${status.error}`;
}

async function loadMetadata() {
    try {
        const response = await fetch('/examples');
        if (!response.ok) return;
        const data = await response.json();
        setBadge(data.mode);
        renderSuggestions(data.examples || []);
    } catch (error) {
        console.error('Metadata load failed', error);
    }
}

async function askQuestion() {
    const question = userInput.value.trim();
    if (!question || isLoading) return;

    addMessage(question, 'user');
    userInput.value = '';
    resetSteps();
    const systemMsg = addMessage('Analizando datos...', 'system');
    setLoading(true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        });

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(errorPayload.detail || 'La consulta fallo antes de iniciar el streaming.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const frames = buffer.split('\n\n');
            buffer = frames.pop() || '';

            for (const frame of frames) {
                const line = frame
                    .split('\n')
                    .find((entry) => entry.startsWith('data: '));
                if (!line) continue;

                const payload = line.slice(6).trim();
                if (payload === '[DONE]') continue;

                try {
                    updateUI(JSON.parse(payload), systemMsg);
                } catch (error) {
                    console.error('Failed to parse stream chunk', error, payload);
                }
            }
        }
    } catch (error) {
        systemMsg.textContent = `Lo siento, ocurrio un error: ${error.message}`;
        console.error(error);
    } finally {
        setLoading(false);
        userInput.focus();
    }
}

sendBtn.addEventListener('click', askQuestion);
userInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') askQuestion();
});

function fillInput(text) {
    userInput.value = text;
    askQuestion();
}

window.fillInput = fillInput;
loadMetadata();
