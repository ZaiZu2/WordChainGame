import Container from "react-bootstrap/Container";
import Stack from "react-bootstrap/Stack";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Chat from "./components/Chat";
import Header from "./components/Header";
import { LoginModal } from "./components/NewPlayerModal";
import RoomRulesModal from "./components/RoomRulesModal";
import RulesDescription from "./components/RulesDescription";
import { useStore } from "./contexts/storeContext";
import { WebSocketProvider } from "./contexts/WebsocketProvider";
import LobbyPage from "./pages/LobbyPage";
import RoomPage from "./pages/RoomPage";

export default function App() {
    const { player, modalConfigs } = useStore();

    return (
        <BrowserRouter>
            {!player ? (
                <LoginModal />
            ) : (
                <>
                    {modalConfigs.roomRules && (
                        <RoomRulesModal
                            disabledFields={modalConfigs.roomRules.disabledFields}
                            defaultValues={modalConfigs.roomRules.defaultValues}
                            onSubmit={modalConfigs.roomRules.onSubmit}
                        />
                    )}
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
                                    <Route path="/room" element={<RoomPage />} />
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
