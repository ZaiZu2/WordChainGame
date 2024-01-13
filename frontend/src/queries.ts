import { BASE_API_URL } from './config'
import { GameRoom } from './types'

export async function getGameRooms(): Promise<GameRoom[]> {
    const response = await fetch(BASE_API_URL + '/games')
    if (response.ok) {
        return response.json();
    }
    else {
        throw Error('Error fetching games');
    }
}