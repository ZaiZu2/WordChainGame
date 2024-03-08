import { useState } from "react";

import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import { Button, Stack } from "react-bootstrap";
import { Link } from "react-router-dom";

import GamePage from "../pages/GamePage";
import { usePlayer } from "../contexts/PlayerContext";
import NewRoomModal from "./NewRoomModal";
import appActor from "../machines/appMachine"
import { useSelector } from '@xstate/react';

export default function Header() {
    const { player, logOut } = usePlayer();

    const [newGameModalVis, setShowNewGameModal] = useState(false);

    return (
        <>
            <NewRoomModal
                show={newGameModalVis}
                setShow={setShowNewGameModal}
            />
            <Navbar className="bg-body-secondary">
                <Container>
                    <Navbar.Brand>Word Chain Game</Navbar.Brand>
                    <Navbar.Toggle />
                    <Navbar.Collapse className="justify-content-end">
                        <Button
                            as={Link as any} // TODO: Requires `react-router-bootstrap` dependency
                            to="/"
                            variant="primary"
                            size="sm"
                            className="me-3"
                        >
                            Lobby
                        </Button>
                        <Button
                            as={Link as any} // TODO: Requires `react-router-bootstrap` dependency
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
                                onClick={() => setShowNewGameModal(true)}
                            >
                                Create room
                            </Button>
                            <Button
                                variant="primary"
                                size="sm"
                                className=""
                                onClick={() => {
                                    appActor.send({ type: 'requestLogOut' })
                                }}
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
