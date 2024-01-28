import Header from "./components/Header";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Container from "react-bootstrap/Container";
import Stack from "react-bootstrap/Stack";

import Chat from "./components/Chat";
import GamePage from "./pages/GamePage";
import LobbyPage from "./pages/LobbyPage";
import Rules from "./components/Rules";
import NewPlayerModal from "./components/NewPlayerModal";
import ApiProvider from "./contexts/ApiContext";
import PlayerProvider from "./contexts/PlayerContext";

export default function App() {
    return (
        <BrowserRouter>
            <ApiProvider>
                <PlayerProvider>
                    <Header />
                    <Container fluid className="p-3">
                        <NewPlayerModal />
                        <Stack gap={3}>
                            <Rules />
                            <Routes>
                                <Route path="/" element={<LobbyPage />} />
                                <Route
                                    path="/game/:gameId"
                                    element={<GamePage />}
                                />
                                <Route path="*" element={<Navigate to="/" />} />
                            </Routes>
                            <Chat />
                        </Stack>
                    </Container>
                </PlayerProvider>
            </ApiProvider>
        </BrowserRouter>
    );
}
