"use strict";

const rates = {
    "USD:EUR": 0.92,
    "EUR:RUB": 105,
    "USD:RUB": 92
};

const form = document.getElementById("convert-form");
const amountInput = document.getElementById("amount");
const fromSelect = document.getElementById("from-currency");
const toSelect = document.getElementById("to-currency");
const resultPanel = document.getElementById("result");
const resultValue = document.getElementById("result-value");
const resultRate = document.getElementById("result-rate");
const message = document.getElementById("message");

function getRate(from, to) {
    if (from === to) {
        return 1;
    }

    const directRate = rates[`${from}:${to}`];
    if (directRate !== undefined) {
        return directRate;
    }

    const reverseRate = rates[`${to}:${from}`];
    return reverseRate === undefined ? null : 1 / reverseRate;
}

function showResult(data, offline = false) {
    const formattedAmount = new Intl.NumberFormat("ru-RU", {
        maximumFractionDigits: 2
    }).format(data.result);

    resultValue.textContent = `${formattedAmount} ${data.to}`;
    resultRate.textContent = `1 ${data.from} = ${new Intl.NumberFormat("ru-RU", {
        maximumFractionDigits: 4
    }).format(data.rate)} ${data.to}`;
    resultPanel.hidden = false;
    message.textContent = offline
        ? "Сервер недоступен. Расчёт выполнен офлайн по фиксированному курсу."
        : "";
    message.classList.remove("error");
}

function showError(text) {
    resultPanel.hidden = true;
    message.textContent = text;
    message.classList.add("error");
}

form.addEventListener("submit", async event => {
    event.preventDefault();
    message.textContent = "";
    message.classList.remove("error");

    const amount = Number(amountInput.value);
    const from = fromSelect.value;
    const to = toSelect.value;

    if (!Number.isFinite(amount) || amount <= 0) {
        showError("Введите положительную сумму.");
        return;
    }

    const query = new URLSearchParams({
        from,
        to,
        amount: String(amount)
    });

    try {
        const response = await fetch(`/api/convert?${query}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Не удалось выполнить конвертацию.");
        }
        showResult(data);
    } catch (error) {
        if (error instanceof TypeError) {
            const rate = getRate(from, to);
            if (rate !== null) {
                showResult({ from, to, amount, result: amount * rate, rate }, true);
                return;
            }
        }

        showError(error instanceof Error ? error.message : "Не удалось выполнить конвертацию.");
    }
});

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/service-worker.js")
            .catch(error => console.error("Не удалось зарегистрировать service worker:", error));
    });
}
