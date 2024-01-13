import { useEffect, useState } from 'react'
import Container from 'react-bootstrap/Container'
import { Button } from 'react-bootstrap'
import Spinner from 'react-bootstrap/Spinner'
import Table from 'react-bootstrap/Table'

import Statistics from '../components/Statistics'
import { BASE_API_URL } from '../config'
import { GameRoom } from '../types'
import { getGameRooms } from '../queries'

export default function LobbyPage() {
    let lobbyStats = {
        active_players: ['Active players', 11],
        active_games: ['Active games', 3],
        longest_chain: ['Longest word chain', 161],
    }

    return (
        <>
            <Statistics stats={lobbyStats} />
            <GameList />
        </>
    )
}


function GameList() {
    const [gameRooms, setGameRooms] = useState();

    useEffect(() => {
        (async () => {
            const gameRooms = await getGameRooms();
            setGameRooms(gameRooms);
        })();
    }, []);

    return (
        <Container className='d-flex flex-column border' style={{ alignItems: 'center' }}>
            <Table borderless className='m-0'>
                <thead>
                    <tr className='d-flex py-2'>
                        <td className='p-0 border-0 fw-bold' style={{ flexGrow: 1, flexBasis: "20%" }} >Name</td>
                        <td className='p-0 border-0 fw-bold' style={{ flexGrow: 1, flexBasis: "20%" }} >Status</td>
                        <td className='p-0 border-0 fw-bold' style={{ flexGrow: 1, flexBasis: "20%" }} >Capacity</td>
                        <td className='p-0 border-0 fw-bold text-center' style={{ flexGrow: 1, flexBasis: "15%" }}>Actions</td>
                    </tr>
                </thead>
                <tbody className='border-top d-flex flex-column'>
                    {
                        gameRooms === undefined ? <Spinner animation="border" className='my-3 mx-auto' /> :
                            gameRooms.length === 0 ? <p className='m-auto'>No games available</p> :
                                gameRooms.map(gameRoom => {
                                    return (
                                        <tr key={gameRoom.id} className='d-flex p-1'>
                                            <td className='p-0 border-0' style={{ flexGrow: 1, flexBasis: "20%" }}>{gameRoom.name}</td>
                                            <td className='p-0 border-0' style={{ flexGrow: 1, flexBasis: "20%" }}>{gameRoom.status}</td>
                                            <td className='p-0 border-0' style={{ flexGrow: 1, flexBasis: "20%" }}>{gameRoom.player_ids.length}/{gameRoom.max_size}</td>
                                            <td className='p-0 border-0 d-flex gap-2' style={{ flexGrow: 1, flexBasis: "15%", flexDirection: "horizontal" }}>
                                                <Button variant='primary' size='sm'>Watch</Button>
                                                <Button variant='primary' size='sm'>Join</Button>
                                            </td>
                                        </tr>
                                    )
                                })
                    }
                </tbody>
            </Table>
        </Container>
    )
}