// Socket.IO connection helper
const socket = io();

socket.on('connect', () => {
    console.log('Connected to UniRide real-time server');
});

socket.on('error', (err) => {
    console.error('Socket error:', err);
});