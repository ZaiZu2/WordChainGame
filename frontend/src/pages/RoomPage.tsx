import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Table from "react-bootstrap/Table";
import { Button, Stack } from "react-bootstrap";
import { useNavigate, useParams } from "react-router-dom";
import Icon from "../components/Icon";
import Statistics from "../components/Statistics";
import { GameState, Player, RoomState, Word } from "../types";
import { useStore } from "../contexts/storeContext";
import apiClient from "../apiClient";
import Tooltip from "../components/Tooltip";
import { useEffect } from "react";

export default function RoomPage() {
    const { mode, roomState } = useStore();
    const navigate = useNavigate();
    const { roomId } = useParams();

    // TODO: Create a guard to prevent entering the room simply by changing the URL
    useEffect(() => {
        console.log("Room stats", mode, roomId, roomState);
        // if (mode !== "room" || roomState?.id !== roomId) {
        //     navigate("/");
        // }
    });

    return (
        <>
            <RoomHeader />
            <Rules />
            <ButtonBar />
            <ScoreCard />
            <WordList />
        </>
    );
}

function RoomHeader() {
    const { roomState } = useStore();
    const icons = [
        {
            symbol: roomState?.status === "Closed" ? "lock" : "lock_open_right",
            tooltip:
                roomState?.status === "Closed"
                    ? "No new players can join the room"
                    : "Players can freely join the room",
            className: "ms-auto",
        },
        {
            symbol: "group",
            value: `${Object.keys(roomState?.players || {}).length}/${roomState?.capacity}`,
            tooltip: "Number of players in the room",
        },
        {
            symbol: "manage_accounts",
            value: roomState?.owner_name,
            tooltip: "Owner of the room",
        },
    ];

    return (
        <Container className="border">
            <Stack direction="horizontal" gap={2} className="py-2">
                <div className="fs-3">{roomState?.name}</div>
                {icons.map((icon, index) => (
                    <>
                        {index !== 0 && <div className="vr" />}
                        <Icon {...icon} />
                    </>
                ))}
            </Stack>
        </Container>
    );
}

function Rules() {
    const { roomState } = useStore();
    const icons = [
        {
            symbol: "skull",
            value: (roomState as RoomState).rules.type === "deathmatch" ? "Deathmatch" : "Error",
            tooltip: "Game type",
        },
        {
            symbol: "history",
            value: (roomState as RoomState)?.rules.round_time,
            tooltip: "Length of a round in seconds",
        },
        {
            symbol: "start",
            value: (roomState as RoomState)?.rules.start_score,
            tooltip: "Amount of points each players starts with",
        },
        {
            symbol: "check",
            value: (roomState as RoomState)?.rules.reward,
            tooltip: "Amount of points awarded for correct word",
        },
        {
            symbol: "dangerous",
            value: (roomState as RoomState)?.rules.penalty,
            tooltip: "Amount of points subtracted due to wrong answer",
        },
    ];

    return (
        <Container className="border">
            <Stack direction="horizontal" gap={2} className="py-2 justify-content-between">
                {icons.map((icon, index) => (
                    <>
                        {index !== 0 && <div className="vr" />}
                        <Icon {...icon} />
                    </>
                ))}
            </Stack>
        </Container>
    );
}

function ButtonBar() {
    const {
        mode,
        player,
        roomState,
        chatMessages,
        setMode,
        updateChatMessages,
        purgeChatMessages,
    } = useStore();
    const navigate = useNavigate();

    async function handleLeaveRoom(roomId: number) {
        const prevMessages = [...chatMessages];
        purgeChatMessages();

        try {
            await apiClient.post(`/rooms/${roomId}/leave`);
        } catch (error) {
            updateChatMessages(prevMessages); // Restore chat messages in case `leave` request fails
            return;
        }
        setMode("lobby");
        navigate("/");
    }

    async function handleToggleRoomStatus(roomId: number) {
        try {
            await apiClient.post(`/rooms/${roomId}/toggle`);
        } catch (error) {
            return;
        }
    }

    return (
        <Container className="border">
            <Stack gap={2} direction="horizontal" className="py-2">
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleLeaveRoom(roomState?.id as number)}
                    className="ms-auto"
                >
                    Leave
                </Button>
                {roomState?.owner_name === player?.name ? (
                    <>
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleToggleRoomStatus(roomState?.id as number)}
                        >
                            {roomState?.status === "Open" ? "Close" : "Open"}
                        </Button>
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleLeaveRoom(roomState?.id as number)}
                        >
                            Edit rules
                        </Button>
                        <Button variant="primary" size="sm" onClick={() => true} disabled={true}>
                            Start
                        </Button>
                    </>
                ) : (
                    <Button variant="primary" size="sm" onClick={() => true} disabled={true}>
                        Ready
                    </Button>
                )}
            </Stack>
        </Container>
    );
}

function ScoreCard() {
    const { mode, roomState, gameState } = useStore();

    const style = {
        flexBasis: "25%",
    };

    return (
        <Container className="border">
            <Table borderless className="m-0 text-center">
                <thead>
                    <tr className="d-flex py-2 justify-content-between">
                        <td style={style} className="p-0 border-0 text-start fw-bold">
                            #
                        </td>
                        <td style={style} className="p-0 border-0 text-end fw-bold">
                            Player
                        </td>
                        {mode === "game" ? (
                            <>
                                <td style={style} className="p-0 border-0 text-end fw-bold">
                                    Points
                                </td>
                                <td style={style} className="p-0 border-0 text-end fw-bold">
                                    Mistakes
                                </td>
                            </>
                        ) : (
                            <td style={style} className="p-0 border-0 text-end fw-bold">
                                Ready
                            </td>
                        )}
                    </tr>
                </thead>
                <tbody className="border-top">
                    {(mode === "room" ? Object.values((roomState as RoomState).players) : [])
                        // : (gameState as GameState).players
                        .map((player, index) => {
                            return (
                                <tr
                                    key={player.name}
                                    className={`d-flex py-1 justify-content-between`}
                                >
                                    <td style={style} className="p-0 border-0 text-start">
                                        {index}
                                    </td>
                                    <td style={style} className="p-0 border-0 text-end">
                                        {player.name}
                                    </td>
                                    {mode === "game" ? (
                                        <>
                                            <td style={style} className="p-0 border-0 text-end">
                                                {/* {gameState.players[player.name].points} */}0
                                            </td>
                                            <td style={style} className="p-0 border-0 text-end">
                                                {/* {gameState.players[player.name].mistakes} */}0
                                            </td>
                                        </>
                                    ) : (
                                        <td style={style} className="p-0 border-0 text-end">
                                            1
                                        </td>
                                    )}
                                </tr>
                            );
                        })}
                </tbody>
            </Table>
        </Container>
    );
}
function WordList() {
    const { roomState } = useStore();

    const positionToSize: Record<number, string> = {
        0: "fs-6",
        1: "fs-5",
        2: "fs-4",
        3: "fs-3",
        4: "fs-2",
        5: "fs-1",
    };
    let symbol = (word: Word) => (word.is_correct ? "check" : "close");
    let points = (word: Word) =>
        word.is_correct ? "+" + roomState?.rules.reward : roomState?.rules.penalty;
    let color = (word: Word) => (word.is_correct ? "text-success" : "text-danger"); // GREEN or RED

    const word_1 = {
        id: 1,
        player_name: "Vecky",
        created_on: new Date("2024-01-01 12:00:00"),
        content: "Elephant",
        is_correct: true,
        game_id: 1,
    } as Word;
    const word_2 = {
        id: 2,
        player_name: "Adam",
        created_on: new Date("2024-01-01 12:00:00"),
        content: "Tiger",
        is_correct: false,
        game_id: 1,
    } as Word;
    const word_3 = {
        id: 3,
        player_name: "Becky",
        created_on: new Date("2024-01-01 12:00:00"),
        content: "Rotor",
        is_correct: false,
        game_id: 1,
    } as Word;
    let words = [word_1, word_2, word_3, word_2, word_1];

    const style = {
        flexGrow: 1,
        flexShrink: 0,
        justifyContent: "center",
        alignItems: "center",
    };

    return (
        <Container className="border">
            <Table borderless className="m-0 text-center">
                <tbody>
                    {words.map((word, position) => {
                        return (
                            <tr style={style} className="d-flex justify-content-between">
                                <td style={{ flexBasis: "20%" }} className="p-0 border-0">
                                    {word.player_name}
                                </td>
                                <td className="p-0 border-0">
                                    <Stack direction="horizontal" gap={2}>
                                        <div
                                            style={{ flexBasis: "60%" }}
                                            className={`p-0 border-0 ${positionToSize[position]}`}
                                        >
                                            {word.content}
                                        </div>
                                        <div
                                            style={{ flexBasis: "10%" }}
                                            className={`p-0 border-0 material-symbols-outlined ${color(
                                                word
                                            )}`}
                                        >
                                            {symbol(word)}
                                        </div>
                                    </Stack>
                                </td>
                                <td
                                    style={{ flexBasis: "10%" }}
                                    className={`p-0 border-0$ ${color(word)}`}
                                >
                                    {points(word)}
                                </td>
                            </tr>
                        );
                    })}
                    <tr style={style} className="d-flex justify-content-between">
                        <td style={{ flexBasis: "20%" }} className="p-0 border-0">
                            Vecky
                        </td>
                        <td
                            style={{ flexBasis: "60%" }}
                            className={`d-flex p-0 border-0 ${positionToSize[5]} justify-content-center`}
                        >
                            <Form.Control
                                type="text"
                                placeholder="Write here..."
                                className="py-1 mt-2 mb-2 w-50"
                            />
                        </td>
                        <td>
                            <Stack direction="horizontal" gap={1}>
                                <div
                                    style={{ flexBasis: "10%" }}
                                    className={`p-0 border-0 material-symbols-outlined`}
                                ></div>
                                <div style={{ flexBasis: "10%" }} className={"p-0 border-0"}></div>
                            </Stack>
                        </td>
                    </tr>
                </tbody>
            </Table>
        </Container>
    );
}
