export type GameRoom = {
    id: number,
    name: string,
    player_uids: string[],
    max_size: number,
    status: ['In progress', 'Open', 'Closed'],
}