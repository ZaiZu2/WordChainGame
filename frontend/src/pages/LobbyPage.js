import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Stack from 'react-bootstrap/Stack'
import { Button } from 'react-bootstrap'
import { Link } from 'react-router-dom'

import Statistics from '../components/Statistics'


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
    const game_1 = {
        id: 1,
        name: 'Game 1',
        players: ['Vecky', 'John', 'Paul', 'George', 'Ringo'],
        maxSize: 5,
        status: 'In progress',
    }
    const game_2 = {
        id: 2,
        name: 'Game 2',
        players: ['Ringo'],
        maxSize: 5,
        status: 'Open',
    }
    const game_3 = {
        id: 3,
        name: 'Game 3',
        players: ['Vecky', 'John', 'Paul', 'George', 'Ringo'],
        maxSize: 5,
        status: 'Closed',
    }
    let games = [game_1, game_2, game_3]

    return (
        <>
            <Container className='border'>
                {games.length === 0 ?
                    <p>No games available</p>
                    :
                    games.map(game => {
                        return (
                            <Stack key={game.id} direction='horizontal' gap={1} className='my-1'>
                                <Container className='p-0'>
                                    <Row>
                                        <Col>{game.name}</Col>
                                        <Col>{game.status}</Col>
                                        <Col>{game.players.length}/{game.maxSize}</Col>
                                    </Row>
                                </Container>
                                < Button variant='primary' size='sm'>Watch</Button>
                                < Button variant='primary' size='sm'>Join</Button>
                            </Stack>
                        )
                    })
                }
            </Container>
        </>
    )
}