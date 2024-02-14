import { useState } from "react";

import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import { Button, Stack } from "react-bootstrap";
import { Link } from "react-router-dom";

import GamePage from "../pages/GamePage";
import { usePlayer } from "../contexts/PlayerContext";
import NewRoomModal from "./NewRoomModal";

export default function Header() {
    const { player, logOut } = usePlayer();

    const [newGameModalVis, setShowNewGameModal] = useState(false);
    const showNewGameModal = () => setShowNewGameModal(true);
    const hideNewGameModal = () => setShowNewGameModal(false);

    return (
        <>
            <NewRoomModal show={newGameModalVis} onHide={hideNewGameModal} />
            <Navbar className="bg-body-secondary">
                <Container>
                    <Navbar.Brand>Word Chain Game</Navbar.Brand>
                    <Navbar.Toggle />
                    <Navbar.Collapse className="justify-content-end">
                        <Button
                            as={Link}
                            to="/"
                            variant="primary"
                            size="sm"
                            className="me-3"
                        >
                            Lobby
                        </Button>
                        <Button
                            as={Link}
                            to="/game/1"
                            elements={<GamePage />}
                            variant="primary"
                            size="sm"
                            className="me-3"
                        >
                            Game
                        </Button>

                        <Stack gap={3} direction="horizontal">
                            <Navbar.Text className="m-0 fs-4">
                                {player ? player.name : "???"}
                            </Navbar.Text>
                            <Button
                                variant="primary"
                                size="sm"
                                onClick={showNewGameModal}
                            >
                                Create room
                            </Button>
                            <Button
                                variant="primary"
                                size="sm"
                                className=""
                                onClick={logOut}
                            >
                                Log out
                            </Button>
                        </Stack>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
        </>
    );
}
