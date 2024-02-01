import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Container from "react-bootstrap/Container";
import Stack from "react-bootstrap/Stack";

import Header from "./components/Header";
import Chat from "./components/Chat";
import GamePage from "./pages/GamePage";
import LobbyPage from "./pages/LobbyPage";
import Rules from "./components/Rules";
import { LoginModal, SuccessfulLoginModal } from "./components/NewPlayerModal";
import { usePlayer } from "./contexts/PlayerContext";

export default function App() {
    const { player } = usePlayer();

    const [showNewPlayerModal, setShowNewPlayerModal] = useState(true);

    return (
        <BrowserRouter>
            <Header />
            <Container fluid className="p-3">
                {!player ? (
                    <LoginModal />
                ) : (
                    <Stack gap={3}>
                        <Container>
                            <div className="text-center fs-6">
                                Use this code to log into your account again
                            </div>
                            <div className="text-center mt-2 fs-5">
                                {player?.id}
                            </div>
                        </Container>
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
                )}
            </Container>
        </BrowserRouter>
    );
}
