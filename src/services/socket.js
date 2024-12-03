import { io } from 'socket.io-client';
import { ref, reactive } from 'vue';

const DEFAULT_URL = import.meta.env.VITE_FLASK_HUB_URL || 'http://localhost:5001';

// Reactive connection state
export const connectionState = reactive({
  connected: false,
  connecting: false,
  error: null,
  reconnectAttempts: 0,
  currentUrl: ''
});

// Socket instance (singleton)
let socket = null;

export function initSocket(url = null) {
  const targetUrl = url || localStorage.getItem('websocket_url') || DEFAULT_URL;

  // If already connected to same URL, return existing socket
  if (socket && connectionState.currentUrl === targetUrl) {
    return socket;
  }

  // If connected to different URL, disconnect first
  if (socket) {
    socket.disconnect();
    socket = null;
  }

  connectionState.connecting = true;
  connectionState.currentUrl = targetUrl;

  socket = io(targetUrl, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000
  });

  // Connection lifecycle
  socket.on('connect', () => {
    console.log('[Socket] Connected:', socket.id);
    connectionState.connected = true;
    connectionState.connecting = false;
    connectionState.error = null;
    connectionState.reconnectAttempts = 0;
  });

  socket.on('disconnect', (reason) => {
    console.log('[Socket] Disconnected:', reason);
    connectionState.connected = false;
    if (reason === 'io server disconnect') {
      // Server initiated disconnect, try to reconnect
      socket.connect();
    }
  });

  socket.on('connect_error', (error) => {
    console.error('[Socket] Connection error:', error);
    connectionState.connecting = false;
    connectionState.error = error.message;
  });

  socket.io.on('reconnect_attempt', (attempt) => {
    console.log('[Socket] Reconnection attempt:', attempt);
    connectionState.reconnectAttempts = attempt;
    connectionState.connecting = true;
  });

  socket.io.on('reconnect', (attempt) => {
    console.log('[Socket] Reconnected after', attempt, 'attempts');
  });

  socket.io.on('reconnect_failed', () => {
    console.error('[Socket] Reconnection failed');
    connectionState.error = 'Failed to reconnect after maximum attempts';
  });

  return socket;
}

export function getSocket() {
  if (!socket) {
    return initSocket();
  }
  return socket;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
    connectionState.connected = false;
    connectionState.currentUrl = '';
  }
}

export function reconnectSocket(newUrl) {
  console.log('[Socket] Reconnecting to:', newUrl);
  disconnectSocket();
  return initSocket(newUrl);
}

// Typed emit helpers
export function emitParamsUpdate(params) {
  const s = getSocket();
  s.emit('params_update', { params });
}

export function emitChatRequest(prompt, params, username = null, apiKey = null, model = null) {
  const s = getSocket();
  s.emit('chat_request', { prompt, params, username, api_key: apiKey, model });
}
