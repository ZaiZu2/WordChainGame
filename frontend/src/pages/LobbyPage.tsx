import { useEffect } from "react";
import { Button, Stack } from "react-bootstrap";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";
import { useNavigate } from "react-router-dom";

import apiClient from "../apiClient";
import Bubble from "../components/Bubble";
import Icon from "../components/Icon";
import IconBar from "../components/IconBar";
import { useStore } from "../contexts/storeContext";
import { RoomOut, RoomState } from "../types";
import { AllTimeStatistics, LobbyState } from "../types";
import { castToMinutes } from "../utils";

export default function LobbyPage() {
    const { toggleModal } = useStore();

    return (
        <>
            <Statistics />
            <Bubble>
                <Stack gap={2} direction="horizontal">
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                            toggleModal("roomRules", { onSubmit: "POST" });
                        }}
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

export function Statistics() {
    const {
        lobbyState: _lobbyState,
        allTimeStatistics: _allTimeStatistics,
        setAllTimeStatistics,
    } = useStore();
    const lobbyState = _lobbyState as LobbyState;
    const allTimeStatistics = _allTimeStatistics as AllTimeStatistics;

    const elements = [
        {
            symbol: "groups",
            value: lobbyState?.stats.active_players,
            tooltip: "Number of players currently online",
        },
        {
            symbol: "holiday_village",
            value: lobbyState?.stats.active_rooms,
            tooltip: "Number of rooms currently active",
        },
        {
            symbol: "link",
            value: allTimeStatistics?.longest_chain,
            tooltip: "The longest chain of words built in a single game",
        },
        {
            symbol: "history",
            value: castToMinutes(allTimeStatistics?.longest_game_time),
            tooltip: "The longest time a game was played",
        },
        {
            symbol: "joystick",
            value: allTimeStatistics?.total_games,
            tooltip: "Number of Word Chain games ever played",
        },
    ];

    useEffect(() => {
        const fetchStats = async () => {
            const allTimeStatistics = (await apiClient.get<AllTimeStatistics>("/stats")).body;
            setAllTimeStatistics(allTimeStatistics);
        };

        // Fetch stats immediately and then every 60 seconds
        fetchStats();
        const intervalId = setInterval(fetchStats, 60 * 1000);

        // Clean up the interval on unmount
        return () => clearInterval(intervalId);
    }, []);

    return (
        <Bubble>
            <IconBar elements={elements} />
        </Bubble>
    );
}

function RoomList() {
    const navigate = useNavigate();
    const {
        switchMode,
        lobbyState,
        chatMessages,
        updateChatMessages,
        purgeChatMessages,
        updateRoomState,
    } = useStore();
    const rooms = lobbyState?.rooms as Record<number, RoomOut>;

    async function handleJoinRoom(roomId: number) {
        const prevMessages = [...chatMessages];
        purgeChatMessages();

        let response;
        try {
            response = await apiClient.post<RoomState>(`/rooms/${roomId}/join`);
        } catch (error) {
            updateChatMessages(prevMessages); // Restore chat messages in case `join` request fails
            return;
            // TODO: Inform user about the error
        }
        updateRoomState(response.body);
        switchMode("room");
        navigate(`/room`);
    }

    return (
        <Bubble>
            <Table borderless size="sm" className="m-0">
                <thead className="border-bottom">
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
                    <tr style={{ height: "0.5rem" }}></tr>
                </thead>
                <tbody>
                    <tr style={{ height: "0.5rem" }}></tr>
                    {rooms !== undefined && Object.values(rooms).length === 0 && (
                        <tr>
                            <td colSpan={4} className="p-1 ms-auto text-center">
                                No rooms available
                            </td>
                        </tr>
                    )}
                    {rooms !== undefined && Object.values(rooms).length !== 0 && (
                        <>
                            {Object.values(rooms).map((room) => {
                                return (
                                    <tr key={room.id}>
                                        <td>{room.name}</td>
                                        <td>
                                            <Icon
                                                symbol={
                                                    room.status === "Closed"
                                                        ? "lock"
                                                        : room.status === "In progress"
                                                        ? "clock_loader_40"
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
            {rooms === undefined && (
                <div className="text-center">
                    <Spinner animation="border" className="my-3 mx-auto" />
                </div>
            )}
        </Bubble>
    );
}
