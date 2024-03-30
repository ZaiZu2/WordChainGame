import Container from "react-bootstrap/Container";
import { Button, Stack } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";
import { useNavigate } from "react-router-dom";

import Statistics from "../components/Statistics";
import apiClient from "../apiClient";
import { RoomState, RoomOut } from "../types";
import { useStore } from "../contexts/storeContext";
import Bubble from "../components/Bubble";

export default function LobbyPage() {
    const { toggleCreateRoomModal } = useStore();

    return (
        <>
            <Statistics />
            <Bubble>
                <Stack gap={2} direction="horizontal">
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => toggleCreateRoomModal(true)}
                        className="ms-auto"
                    >
                        Create room
                    </Button>
                </Stack>
            </Bubble>
            <RoomList />
        </>
    );
}

function RoomList() {
    const navigate = useNavigate();
    const { setMode, lobbyState, chatMessages, updateChatMessages, purgeChatMessages } = useStore();
    const rooms = lobbyState?.rooms as Record<number, RoomOut>;

    async function handleJoinRoom(roomId: number) {
        const prevMessages = [...chatMessages];
        purgeChatMessages();

        try {
            await apiClient.post<RoomState>(`/rooms/${roomId}/join`);
        } catch (error) {
            updateChatMessages(prevMessages); // Restore chat messages in case `join` request fails
            return;
        }
        setMode("room");
        navigate(`/rooms/${roomId}`);
    }

    return (
        <Bubble>
            <Table borderless className="m-0 pt-0">
                <thead>
                    <tr className="d-flex">
                        <td
                            className="p-0 border-0 flex-grow-1 fw-bold"
                            style={{ flexBasis: "20%" }}
                        >
                            Name
                        </td>
                        <td
                            className="p-0 border-0 flex-grow-1 fw-bold"
                            style={{ flexBasis: "20%" }}
                        >
                            Status
                        </td>
                        <td
                            className="p-0 border-0 flex-grow-1 fw-bold"
                            style={{ flexBasis: "20%" }}
                        >
                            Capacity
                        </td>
                        <td
                            className="p-0 border-0 flex-grow-1 fw-bold"
                            style={{ flexBasis: "20%" }}
                        >
                            Owner
                        </td>
                        <td
                            className="p-0 border-0 flex-grow-1 fw-bold text-end"
                            style={{ flexBasis: "15%" }}
                        >
                            Actions
                        </td>
                    </tr>
                </thead>
                <tbody className="border-top pt-2 d-flex flex-column gap-2">
                    {rooms === undefined ? (
                        <Spinner animation="border" className="my-3 mx-auto" />
                    ) : Object.values(rooms).length === 0 ? (
                        <tr>
                            <td className="p-1 m-auto">No games available</td>
                        </tr>
                    ) : (
                        Object.values(rooms).map((room) => {
                            return (
                                <tr key={room.id} className="d-flex">
                                    <td
                                        className="p-0 border-0 flex-grow-1"
                                        style={{ flexBasis: "20%" }}
                                    >
                                        {room.name}
                                    </td>
                                    <td
                                        className="p-0 border-0 flex-grow-1"
                                        style={{ flexBasis: "20%" }}
                                    >
                                        {room.status}
                                    </td>
                                    <td
                                        className="p-0 border-0 flex-grow-1"
                                        style={{ flexBasis: "20%" }}
                                    >
                                        {room.players_no}/{room.capacity}
                                    </td>
                                    <td
                                        className="p-0 border-0 flex-grow-1"
                                        style={{ flexBasis: "20%" }}
                                    >
                                        {room.owner_name}
                                    </td>
                                    <td
                                        className="p-0 border-0 flex-grow-1 d-flex gap-2 justify-content-end"
                                        style={{ flexBasis: "15%" }}
                                    >
                                        <Button variant="primary" size="sm" disabled>
                                            Watch
                                        </Button>
                                        <Button
                                            onClick={() => handleJoinRoom(room.id as number)}
                                            variant="primary"
                                            size="sm"
                                            disabled={
                                                room.players_no === room.capacity ||
                                                !(room.status === "Open")
                                            }
                                        >
                                            Join
                                        </Button>
                                    </td>
                                </tr>
                            );
                        })
                    )}
                </tbody>
            </Table>
        </Bubble>
    );
}
