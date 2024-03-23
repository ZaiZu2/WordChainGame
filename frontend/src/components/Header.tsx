import { useState } from "react";

import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import { Button, Stack } from "react-bootstrap";
import { Link } from "react-router-dom";

import RoomPage from "../pages/RoomPage";
import { useStore } from "../contexts/storeContext";
import NewRoomModal from "./NewRoomModal";

export default function Header() {
    const { player, logOut } = useStore();

    const [newGameModalVis, setShowNewGameModal] = useState(false);

    return (
        <>
            <NewRoomModal show={newGameModalVis} setShow={setShowNewGameModal} />
            <Navbar className="bg-body-secondary">
                <Container>
                    <Navbar.Brand>Word Chain Game</Navbar.Brand>
                    <Navbar.Toggle />
                    <Navbar.Collapse className="justify-content-end">
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
                            <Button variant="primary" size="sm" className="" onClick={logOut}>
                                Log out
                            </Button>
                        </Stack>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
        </>
    );
}
