import {Injectable} from '@angular/core';
import * as io from 'socket.io-client';
import {environment} from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SocketIOService {
  private socketUrl = environment.socketioUrl;

  private opts = {
    transportOptions: {
      transports: ['polling'] // , 'websocket']
    }
  };

  constructor() {
  }

  connect(namespace: string): SocketIOClient.Socket {
    const socket = io(`${this.socketUrl}/${namespace}`, this.opts);
    socket.on('connect', () => {
      console.log(`Socket connection to namespace /${namespace} established`);
    });
    socket.on('connect_error', (error) => {
      console.log(`Socket connection to namespace /${namespace} failed:\n${error}`);
    });
    socket.on('connect_timeout', (timeout) => {
      console.log(`Connection timeout on namespace /${namespace}: ${timeout}`);
    });
    socket.on('error', (error) => {
      console.log(`Error on namespace /${namespace}: ${error}`);
    });
    socket.on('reconnect', (attempt) => {
      console.log(`Reconnected to namespace /${namespace}: Took ${attempt} attempts`);
    });
    socket.on('reconnect_attempt', (attempt) => {
      console.log(`Reconnecting attempt to namespace /${namespace}: Attempt ${attempt}`);
    });
    socket.on('reconnect_error', (error) => {
      console.log(`Error reconnecting to namespace /${namespace}: ${error}`);
    });
    socket.on('reconnect_attempt', (attempt) => {
      console.log(`Reconnecting attempt to namespace /${namespace}: Attempt ${attempt}`);
    });
    socket.on('reconnect_failed', () => {
      console.log(`Reconnect to namespace /${namespace} failed`);
    });
    socket.on('disconnect', (reason) => {
      if (reason === 'io server disconnect') {
        // the disconnection was initiated by the server, you need to reconnect manually
        console.log(`Server on namespace /${namespace} disconnected`);
      }
      // else the socket will automatically try to reconnect
    });

    return socket;
  }

  disconnect(socket: SocketIOClient.Socket) {
    socket.disconnect()
  }
}
