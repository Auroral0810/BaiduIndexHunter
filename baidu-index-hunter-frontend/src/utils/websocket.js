import { io } from 'socket.io-client';
import { ref } from 'vue';

const SOCKET_URL = 'http://127.0.0.1:5001';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = ref(false);
    this.listeners = new Map();
  }

  connect() {
    if (this.socket) return;

    this.socket = io(SOCKET_URL, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.connected.value = true;
      this.notifyListeners('connect', true);
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.connected.value = false;
      this.notifyListeners('disconnect', false);
    });

    this.socket.on('task_update', (data) => {
      console.log('Received task update:', data);
      this.notifyListeners('task_update', data);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index !== -1) {
      callbacks.splice(index, 1);
    }
  }

  notifyListeners(event, data) {
    if (!this.listeners.has(event)) return;
    this.listeners.get(event).forEach(callback => callback(data));
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected.value = false;
    }
  }
}

export const webSocketService = new WebSocketService();
