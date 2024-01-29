import { useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import { Button } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";

import Statistics from "../components/Statistics";
import { getGameRooms } from "../queries";
import { useApi } from "../contexts/ApiContext";
import { GameRoom } from "../types";

export default function LobbyPage() {
    let lobbyStats = {
        active_players: ["Active players", 11],
        active_games: ["Active games", 3],
        longest_chain: ["Longest word chain", 161],
    };

    return (
        <>
            <Statistics stats={lobbyStats} />
            <GameList />
        </>
    );
}

function GameList() {
    const api = useApi();
    const [gameRooms, setGameRooms] = useState<GameRoom[] | undefined>();

    useEffect(() => {
        (async () => {
            const response = await api.get<GameRoom[]>("game_rooms");
            setGameRooms(response.body);
        })();
    }, []);

    return (
        <Container className="d-flex flex-column border" style={{ alignItems: "center" }}>
            <Table borderless className="m-0">
                <thead>
                    <tr className="d-flex py-2">
                        <td className="p-0 border-0 flex-grow-1 fw-bold" style={{ flexBasis: "20%" }}>
                            Name
                        </td>
                        <td className="p-0 border-0 flex-grow-1 fw-bold" style={{ flexBasis: "20%" }}>
                            Status
                        </td>
                        <td className="p-0 border-0 flex-grow-1 fw-bold" style={{ flexBasis: "20%" }}>
                            Capacity
                        </td>
                        <td className="p-0 border-0 flex-grow-1 fw-bold text-center" style={{ flexBasis: "15%" }}>
                            Actions
                        </td>
                    </tr>
                </thead>
                <tbody className="border-top py-2 d-flex flex-column gap-2">
                    {gameRooms === undefined ? (
                        <Spinner animation="border" className="my-3 mx-auto" />
                    ) : gameRooms.length === 0 ? (
                        <p className="p-1 m-auto">No games available</p>
                    ) : (
                        gameRooms.map((gameRoom) => {
                            return (
                                <tr key={gameRoom.id} className="d-flex">
                                    <td className="p-0 border-0 flex-grow-1" style={{ flexBasis: "20%" }}>
                                        {gameRoom.name}
                                    </td>
                                    <td className="p-0 border-0 flex-grow-1" style={{ flexBasis: "20%" }}>
                                        {gameRoom.name}
                                    </td>
                                    <td className="p-0 border-0 flex-grow-1" style={{ flexBasis: "20%" }}>
                                        {gameRoom.name}/{gameRoom.name}
                                    </td>
                                    <td className="p-0 border-0 flex-grow-1 d-flex gap-2" style={{ flexBasis: "15%" }}>
                                        <Button variant="primary" size="sm">
                                            Watch
                                        </Button>
                                        <Button variant="primary" size="sm">
                                            Join
                                        </Button>
                                    </td>
                                </tr>
                            );
                        })
                    )}
                </tbody>
            </Table>
        </Container>
    );
}
