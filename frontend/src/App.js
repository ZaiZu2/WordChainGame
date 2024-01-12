import Header from './components/Header'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Container from 'react-bootstrap/Container'
import Stack from 'react-bootstrap/Stack'

import Chat from './components/Chat'
import Lobby from './pages/LobbyPage'
import Game from './pages/GamePage'

export default function App() {
    return (
        <>
            <Header />
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
        </>
    );
}

