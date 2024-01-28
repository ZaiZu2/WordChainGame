import Container from "react-bootstrap/Container"
import Navbar from "react-bootstrap/Navbar"
import { Button, Stack } from "react-bootstrap"
import { Link } from "react-router-dom"

import GamePage from "../pages/GamePage"
import { usePlayer } from "../contexts/PlayerContext"

export default function Header() {
    const { player, logOut } = usePlayer();

    return (
        <Navbar className="bg-body-secondary">
            <Container>
                <Navbar.Brand href="#home">Word Chain Game</Navbar.Brand>
                <Navbar.Toggle />
                <Navbar.Collapse className="justify-content-end">
                    <Button
                        as={Link}
                        to="/"
                        end
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
                    <Button variant="primary" size="sm" className="me-3">
                        Create room
                    </Button>
                    <Stack gap={3} direction="horizontal">
                        <Navbar.Text className="m-0 fs-3">
                            {player ? player.name : "???"}
                        </Navbar.Text>
                        <Navbar.Text>
                            {player ? `#${player.id.slice(0, 8)}` : "#???"}
                        </Navbar.Text>
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
    );
}
