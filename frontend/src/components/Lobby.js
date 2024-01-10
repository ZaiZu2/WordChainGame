import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Stack from 'react-bootstrap/Stack'
import { Button } from 'react-bootstrap'

export default function Lobby() {
    return (
        <>
            <Container className='border'>
                <Statistics />
            </Container>
            <Container className='border'>
                <GameList />
            </Container>
        </>

    )
}

function Statistics() {
    const stats = {
        active_players: 11,
        active_games: 3,
    }

    return (
        <Container className='p-0'>
            <Row>
                <Col>Active games: {stats.active_games}</Col>
                <Col>Active users: {stats.active_players}</Col>
            </Row>
        </Container >
    )
}

function GameList() {
    const game_1 = {
        id: 1,
        name: 'Game 1',
        players: ['Vecky', 'John', 'Paul', 'George', 'Ringo'],
        max_size: 5,
        status: 'In progress',
    }
    const game_2 = {
        id: 2,
        name: 'Game 2',
        players: ['Ringo'],
        max_size: 5,
        status: 'Open',
    }
    const game_3 = {
        id: 3,
        name: 'Game 3',
        players: ['Vecky', 'John', 'Paul', 'George', 'Ringo'],
        max_size: 5,
        status: 'Closed',
    }
    let games = [game_1, game_2, game_3]

    return (
        <>
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
                                    <Col>{game.players.length}/{game.max_size}</Col>
                                </Row>
                            </Container>
                            < Button variant='primary' size='sm'>Watch</Button>
                            < Button variant='primary' size='sm'>Join</Button>
                        </Stack>

                    )
                })
            }
        </>
    )
}