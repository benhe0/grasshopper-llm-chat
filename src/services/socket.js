import { io } from 'socket.io-client';

const DEFAULT_URL = 'http://localhost:5001';

let socket = null;

export function initSocket(url = DEFAULT_URL) {
  // TODO: implement proper connection handling
  socket = io(url);

  socket.on('connect', () => {
    console.log('Connected to server');
  });

  socket.on('disconnect', () => {
    console.log('Disconnected');
  });

  return socket;
}

export function getSocket() {
  return socket;
}
