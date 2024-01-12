import Container from 'react-bootstrap/Container'
import Stack from 'react-bootstrap/Stack'

import Chat from './Chat'
import Lobby from './LobbyPage'
import Game from './GamePage'

export default function Body() {
    return (
        <Container fluid className='p-3'>
            <Stack gap={3}>
                <Container className='border'>
                    The objective of the game is to form a chain of words where each word starts with the last letter of the
                    previous word.
                </Container>
                <Game />
                <Lobby />
                <Chat />
            </Stack>
        </Container>
    )
}