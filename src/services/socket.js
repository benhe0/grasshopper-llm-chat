import { io } from 'socket.io-client';
import { reactive } from 'vue';

const DEFAULT_URL = 'http://localhost:5001';

export const connectionState = reactive({
  connected: false,
  error: null,
});

let socket = null;

export function initSocket(url = DEFAULT_URL) {
  if (socket) return socket;

  socket = io(url, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 10,
  });

  socket.on('connect', () => {
    console.log('[Socket] Connected');
    connectionState.connected = true;
    connectionState.error = null;
  });

  socket.on('disconnect', () => {
    console.log('[Socket] Disconnected');
    connectionState.connected = false;
  });

  socket.on('connect_error', (err) => {
    console.error('[Socket] Error:', err);
    connectionState.error = err.message;
  });

  return socket;
}

export function getSocket() {
  if (!socket) return initSocket();
  return socket;
}

export function emitParamsUpdate(params) {
  const s = getSocket();
  s.emit('params_update', { params });
}

export function emitChatRequest(prompt, params) {
  const s = getSocket();
  s.emit('chat_request', { prompt, params });
}
