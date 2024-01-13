import { BASE_API_URL } from './config'
import { GameRoom } from './types'

export async function getGameRooms(): Promise<GameRoom[] | null> {
    const response = await fetch(BASE_API_URL + '/games')
    if (response.ok) {
        return response.json();
    }
    else {
        return null;
    }
}