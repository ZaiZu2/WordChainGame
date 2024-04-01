import Container from "react-bootstrap/Container";
import { Button, Stack } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";
import { useNavigate } from "react-router-dom";
import Icon from "../components/Icon";

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
            <Table borderless size="sm" className="m-0">
                <thead>
                    <tr>
                        <td>
                            <Icon symbol="home" tooltip="Name" iconSize={4} />
                        </td>
                        <td>
                            <Icon symbol="shield_person" tooltip="Status" iconSize={4} />
                        </td>
                        <td>
                            <Icon symbol="group" tooltip="Capacity" iconSize={4} />
                        </td>
                        <td>
                            <Icon symbol="manage_accounts" tooltip="Owner" iconSize={4} />
                        </td>
                    </tr>
                    <tr style={{ height: "0.25rem" }} />
                </thead>
                <tbody className="border-top">
                    {rooms === undefined ? (
                        <Spinner animation="border" className="my-3 mx-auto" />
                    ) : Object.values(rooms).length === 0 ? (
                        <tr>
                            <td className="p-1 m-auto">No games available</td>
                        </tr>
                    ) : (
                        <>
                            <tr style={{ height: "0.25rem" }} />
                            {Object.values(rooms).map((room) => {
                                return (
                                    <tr key={room.id}>
                                        <td>{room.name}</td>
                                        <td>
                                            <Icon
                                                symbol={
                                                    room.status === "Closed"
                                                        ? "lock"
                                                        : "lock_open_right"
                                                }
                                                tooltip={room.status}
                                                iconSize={4}
                                            />
                                        </td>
                                        <td>
                                            {room.players_no}/{room.capacity}
                                        </td>
                                        <td>{room.owner_name}</td>
                                        <td>
                                            <Stack
                                                direction="horizontal"
                                                gap={2}
                                                className="justify-content-end"
                                            >
                                                <Button variant="primary" size="sm" disabled>
                                                    Watch
                                                </Button>
                                                <Button
                                                    onClick={() =>
                                                        handleJoinRoom(room.id as number)
                                                    }
                                                    variant="primary"
                                                    size="sm"
                                                    disabled={
                                                        room.players_no === room.capacity ||
                                                        !(room.status === "Open")
                                                    }
                                                >
                                                    Join
                                                </Button>
                                            </Stack>
                                        </td>
                                    </tr>
                                );
                            })}
                        </>
                    )}
                </tbody>
            </Table>
        </Bubble>
    );
}
