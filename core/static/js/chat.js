(function() {
    'use strict';

    var chatRoom = document.getElementById('chat-room');
    if (!chatRoom) return;

    var conversaId = chatRoom.dataset.conversaId;
    var membroId = parseInt(chatRoom.dataset.membroId, 10);
    var pusherKey = chatRoom.dataset.pusherKey;
    var pusherCluster = chatRoom.dataset.pusherCluster;

    var messagesContainer = document.getElementById('chat-messages');
    var chatInput = document.getElementById('chat-input');
    var sendBtn = document.getElementById('chat-send');
    var csrfToken = chatRoom.querySelector('[name=csrfmiddlewaretoken]').value;

    var lastMessageId = 0;
    // Set lastMessageId from existing messages
    var existingBubbles = messagesContainer.querySelectorAll('.chat-bubble');
    if (existingBubbles.length > 0) {
        // We track by counting; the API uses IDs from the server
        lastMessageId = existingBubbles.length;
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function formatTime(isoString) {
        var d = new Date(isoString);
        var h = d.getHours().toString().padStart(2, '0');
        var m = d.getMinutes().toString().padStart(2, '0');
        return h + ':' + m;
    }

    function appendMessage(data, isMine) {
        // Remove empty state message if present
        var emptyMsg = messagesContainer.querySelector('.chat-empty');
        if (emptyMsg) emptyMsg.remove();

        var div = document.createElement('div');
        div.className = 'chat-bubble ' + (isMine ? 'chat-bubble-mine' : 'chat-bubble-other');
        div.dataset.messageId = data.id || '';

        if (!isMine && data.autor_nome) {
            var authorSpan = document.createElement('span');
            authorSpan.className = 'chat-bubble-author';
            authorSpan.textContent = data.autor_nome;
            div.appendChild(authorSpan);
        }

        var textP = document.createElement('p');
        textP.style.margin = '0';
        textP.textContent = data.conteudo;
        div.appendChild(textP);

        var timeSpan = document.createElement('span');
        timeSpan.className = 'chat-bubble-time';
        timeSpan.textContent = formatTime(data.data_envio);
        div.appendChild(timeSpan);

        messagesContainer.appendChild(div);
    }

    function sendMessage() {
        var conteudo = chatInput.value.trim();
        if (!conteudo) return;

        chatInput.value = '';
        chatInput.focus();

        // Optimistic UI
        var now = new Date().toISOString();
        appendMessage({
            autor_id: membroId,
            conteudo: conteudo,
            data_envio: now
        }, true);
        scrollToBottom();

        fetch('/api/chat/' + conversaId + '/enviar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ conteudo: conteudo })
        }).catch(function(err) {
            console.error('Erro ao enviar mensagem:', err);
        });
    }

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Pusher real-time
    if (pusherKey && typeof Pusher !== 'undefined') {
        var pusher = new Pusher(pusherKey, {
            cluster: pusherCluster,
            authEndpoint: '/api/pusher/auth/',
            auth: {
                headers: { 'X-CSRFToken': csrfToken }
            }
        });

        var channel = pusher.subscribe('private-conversa-' + conversaId);

        channel.bind('nova-mensagem', function(data) {
            // Don't duplicate our own messages (already added optimistically)
            if (data.autor_id === membroId) return;
            appendMessage(data, false);
            scrollToBottom();
        });
    } else {
        // Fallback: polling every 5 seconds
        var knownIds = {};
        // Mark existing messages as known
        var serverMessages = messagesContainer.querySelectorAll('.chat-bubble[data-message-id]');
        serverMessages.forEach(function(el) {
            if (el.dataset.messageId) {
                knownIds[el.dataset.messageId] = true;
            }
        });

        setInterval(function() {
            fetch('/api/chat/' + conversaId + '/mensagens/', {
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var msgs = data.mensagens || [];
                var added = false;
                msgs.forEach(function(m) {
                    if (!knownIds[m.id]) {
                        knownIds[m.id] = true;
                        if (m.autor_id !== membroId) {
                            appendMessage(m, false);
                            added = true;
                        }
                    }
                });
                if (added) scrollToBottom();
            })
            .catch(function() {});
        }, 5000);
    }

    // Scroll to bottom on load
    scrollToBottom();
})();
