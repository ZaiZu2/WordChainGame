import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Container from "react-bootstrap/Container";
import Stack from "react-bootstrap/Stack";

import Header from "./components/Header";
import Chat from "./components/Chat";
import RoomPage from "./pages/RoomPage";
import LobbyPage from "./pages/LobbyPage";
import RulesDescription from "./components/RulesDescription";
import { LoginModal } from "./components/NewPlayerModal";
import { useStore } from "./contexts/storeContext";
import { WebSocketProvider } from "./contexts/WebsocketProvider";
import NewRoomModal from "./components/NewRoomModal";

export default function App() {
    const { player } = useStore();

    return (
        <BrowserRouter>
            {!player ? (
                <LoginModal />
            ) : (
                <>
                    <NewRoomModal />
                    <Header />
                    <Container fluid className="p-3">
                        <WebSocketProvider>
                            <Stack gap={3}>
                                <Container>
                                    <div className="text-center fs-6">
                                        Use this code to log into your account again
                                    </div>
                                    <div className="text-center mt-2 fs-5">{player?.id}</div>
                                </Container>
                                <Routes>
                                    <Route path="/" element={<LobbyPage />} />
                                    <Route path="/rooms/:roomId" element={<RoomPage />} />
                                    <Route path="*" element={<Navigate to="/" />} />
                                </Routes>
                                <Chat />
                                <RulesDescription />
                            </Stack>
                        </WebSocketProvider>
                    </Container>
                </>
            )}
        </BrowserRouter>
    );
}
