import { useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import { Button } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";

import Statistics from "../components/Statistics";
import apiClient from "../apiClient";
import { Room } from "../types";
import { useWebSocketContext } from "../contexts/WebsocketProvider"

export default function LobbyPage() {
    let lobbyStats = {
        active_players: ["Active players", 11],
        active_games: ["Active games", 3],
        longest_chain: ["Longest word chain", 161],
    };

    return (
        <>
            <Statistics stats={lobbyStats} />
            <RoomList />
        </>
    );
}

function RoomList() {
    const { rooms } = useWebSocketContext();

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
                        <td className="p-0 border-0 flex-grow-1 fw-bold text-end" style={{ flexBasis: "15%" }}>
                            Actions
                        </td>
                    </tr>
                </thead>
                <tbody className="border-top py-2 d-flex flex-column gap-2">
                    {rooms === undefined ? (
                        <Spinner animation="border" className="my-3 mx-auto" />
                    ) : Object.values(rooms).length === 0 ? (
                        <tr><td className="p-1 m-auto">No games available</td></tr>
                    ) : (
                        Object.values(rooms).map((room) => {
                            return (
                                <tr key={room.id} className="d-flex">
                                    <td className="p-0 border-0 flex-grow-1" style={{ flexBasis: "20%" }}>
                                        {room.name}
                                    </td>
                                    <td className="p-0 border-0 flex-grow-1" style={{ flexBasis: "20%" }}>
                                        {room.status}
                                    </td>
                                    <td className="p-0 border-0 flex-grow-1" style={{ flexBasis: "20%" }}>
                                        {room.players_no}/{room.capacity}
                                    </td>
                                    <td className="p-0 border-0 flex-grow-1 d-flex gap-2 justify-content-end" style={{ flexBasis: "15%" }}>
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
