import { clearErrors, displaySuccess, handleTokenExpired, displayValidationErrors, showErrorPopup } from "./utils.js";

const userAvatar = "https://cdn-icons-png.flaticon.com/512/847/847969.png";
const botAvatar = "https://cdn-icons-png.flaticon.com/512/4712/4712039.png";

const helloMessage = 'Привет! Я бот, который был создан для ресторана VResta. Если хотите узнать все команды, напишите помощь или команды.';

const chatMessages = document.getElementById("chat-messages");
const userInput = document.getElementById("user-input");
const typingIndicator = document.getElementById("typing-indicator");

let isTyping = false;

function addMessage(text, isUser) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageDiv.classList.add(isUser ? "user-message" : "bot-message");

    messageDiv.innerHTML = `
        <img src="${isUser ? userAvatar : botAvatar}" alt="${isUser ? "Аватарка пользователя" : "Аватарка бота"}" class="message-avatar">
        <div class="message-text">${text}</div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage(text, isUser) {
    const token = localStorage.getItem("token");
    const session_id = sessionStorage.getItem("session_id");

    try {
        const response = await fetch("/chat/message", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "session_id": session_id,
                "sender_type": isUser ? "user" : "bot",
                "text": text
            })
        });

        if (isTyping) {
            isTyping = false;
            typingIndicator.style.display = "none";
        }

        if (!response.ok) {
            if (response.status === 401) {
                handleTokenExpired();
            }
            else {
                const errorText = await response.text();
                showErrorPopup("Ошибка при отправке сообщения.");
                console.log(errorText);
            }

            return;
        }

        if (isUser) {
            const json = await response.json();
            addMessage(json.answer);
        }
    }
    catch (error) {
        console.error("Ошибка при отправке сообщения:", error);
        if (isTyping) {
            isTyping = false;
            typingIndicator.style.display = "none";
        }
        showErrorPopup("Ошибка при отправке сообщения.");
    }
}

async function handleSendMessage() {
    const userText = userInput.value.trim();

    if (userText === "" || isTyping) {
        return;
    }

    userInput.value = "";
    isTyping = true;
    typingIndicator.style.display = "flex";

    addMessage(userText, true);
    await sendMessage(userText, true);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function clearChatHistory() {
    if (isTyping) {
        isTyping = false;
        typingIndicator.style.display = "none";
    }

    chatMessages.innerHTML = "";

    const token = localStorage.getItem("token");
    const session_id = sessionStorage.getItem("session_id");

    try {
        const response = await fetch(`/chat/history/${session_id}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                handleTokenExpired();
            }
            else {
                showErrorPopup("Ошибка при очистке истории.");
            }
            return;
        }

        addMessage(helloMessage, false);
        await sendMessage(helloMessage, false);
    }
    catch (error) {
        console.error("Ошибка при очистке истории:", error);
        showErrorPopup("Ошибка при очистке истории.");
    }
}

async function createSession() {
    const token = localStorage.getItem("token");

    try {
        const response = await fetch("/chat/session", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                handleTokenExpired();
            }
            else {
                const errorText = await response.text();
                console.log(errorText);
                showErrorPopup("Ошибка при создании сессии.");
            }
            return;
        }

        const data = await response.json();
        const session_id = data["id"];
        sessionStorage.setItem("session_id", session_id);
    } catch (error) {
        console.error("Ошибка при создании сессии:", error);
        showErrorPopup("Ошибка при создании сессии.");
    }
}

async function loadSessionHistory(session_id) {
    const token = localStorage.getItem("token");

    try {
        const response = await fetch(`/chat/history/${session_id}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                handleTokenExpired();
            }
            else {
                const errorText = await response.text();
                console.log(errorText);
                showErrorPopup("Ошибка при загрузке истории. Попробуйте еще раз.");
            }
            return;
        }

        const messages = await response.json();
        messages.forEach(message => {
            addMessage(message.text, message.sender_type === "user");
        });
    }
    catch (error) {
        console.error("Ошибка при загрузке истории:", error);
        showErrorPopup("Ошибка при загрузке истории.");
    }
}

function setListeners() {
    document.getElementById("send-button").addEventListener("click", handleSendMessage);
    document.getElementById("clear-chat").addEventListener("click", clearChatHistory)

    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            handleSendMessage();
        }
    })

    document.getElementById("authForm").addEventListener("submit", async function(e) {
        e.preventDefault();
        const form = document.getElementById("authForm");

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        clearErrors();

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "username": username,
                    "password": password
                })
            });

            if (!response.ok) {
                if (response.status === 401) {
                    showErrorPopup("Неверный логин или пароль");
                }
                else if (response.status === 422) {
                    const errorData = await response.json();
                    displayValidationErrors(errorData.detail);
                }
                else {
                    showErrorPopup("Ошибка при входе в систему.");
                }
                return;
            }

            const json = await response.json();
            localStorage.setItem("token", json.access_token);

            const session_id = sessionStorage.getItem("session_id");
            if (!session_id) {
                await createSession();

                addMessage(helloMessage, false);
                await sendMessage(helloMessage, false);
            }
            else {
                await loadSessionHistory(session_id);
            }

            document.getElementById("authOverlay").style.display = "none";
        }
        catch (error) {
            console.error("Ошибка при входе:", error);
            showErrorPopup("Ошибка подключения к серверу");
        }
    });

    document.getElementById("registerBtn").addEventListener("click", async function() {
        const form = document.getElementById("authForm");

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        clearErrors();

        try {
            const response = await fetch("/auth/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "username": username,
                    "password": password
                })
            });

            if (!response.ok) {
                if (response.status === 400) {
                    showErrorPopup("Пользователь с таким логином уже существует");
                } else if (response.status === 422) {
                    const errorData = await response.json();
                    displayValidationErrors(errorData.detail);
                }
                return;
            }

            displaySuccess("Регистрация прошла успешно!");
        } catch (error) {
            console.error("Ошибка при регистрации:", error);
            showErrorPopup("Ошибка подключения к серверу");
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    setListeners();

    const token = localStorage.getItem("token");
    if (!token) {
        document.getElementById("authOverlay").style.display = "flex";
        return;
    }

    const session_id = sessionStorage.getItem("session_id");
    if (!session_id) {
        await createSession();
        addMessage(helloMessage, false);
        await sendMessage(helloMessage, false);
    }
    else {
        await loadSessionHistory(session_id);
    }
});
