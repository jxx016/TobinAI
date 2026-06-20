import { Server } from 'http';
import { WebSocketServer } from 'ws';
import { supabase } from './index';
import { AppError } from './middleware/errorHandler';

interface WebSocketClient extends WebSocket {
  isAlive: boolean;
  userId?: string;
}

export const setupWebSocket = (server: Server) => {
  const wss = new WebSocketServer({ server });

  // Heartbeat interval to keep connections alive
  const interval = setInterval(() => {
    wss.clients.forEach((ws: WebSocketClient) => {
      if (!ws.isAlive) {
        return ws.terminate();
      }
      ws.isAlive = false;
      ws.ping();
    });
  }, 30000);

  wss.on('connection', async (ws: WebSocketClient) => {
    ws.isAlive = true;

    ws.on('pong', () => {
      ws.isAlive = true;
    });

    // Handle authentication
    ws.on('message', async (message: string) => {
      try {
        const data = JSON.parse(message);

        if (data.type === 'auth') {
          const token = data.token;
          if (!token) {
            ws.send(JSON.stringify({ type: 'error', message: 'No token provided' }));
            return;
          }

          // Verify token with Supabase
          const { data: { user }, error } = await supabase.auth.getUser(token);
          
          if (error || !user) {
            ws.send(JSON.stringify({ type: 'error', message: 'Invalid token' }));
            return;
          }

          ws.userId = user.id;
          ws.send(JSON.stringify({ type: 'auth', status: 'success' }));
        }
      } catch (error) {
        ws.send(JSON.stringify({ 
          type: 'error', 
          message: error instanceof Error ? error.message : 'Invalid message format' 
        }));
      }
    });

    // Handle client disconnect
    ws.on('close', () => {
      ws.isAlive = false;
    });
  });

  // Cleanup on server shutdown
  wss.on('close', () => {
    clearInterval(interval);
  });

  // Broadcast function to send messages to specific users
  const broadcast = (message: any, userIds: string[]) => {
    wss.clients.forEach((client: WebSocketClient) => {
      if (client.userId && userIds.includes(client.userId)) {
        client.send(JSON.stringify(message));
      }
    });
  };

  return { broadcast };
}; 