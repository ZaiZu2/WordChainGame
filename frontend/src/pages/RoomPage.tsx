import React, { useEffect } from "react";
import { Button, Spinner, Stack } from "react-bootstrap";
import Form from "react-bootstrap/Form";
import Table from "react-bootstrap/Table";
import { useNavigate } from "react-router-dom";

import apiClient from "../apiClient";
import Bubble from "../components/Bubble";
import Icon from "../components/Icon";
import { useStore } from "../contexts/storeContext";
import { GamePlayer, GameState, LobbyState, Player, RoomState, Turn, Word } from "../types";

export default function RoomPage() {
    const { mode } = useStore();
    const navigate = useNavigate();

    useEffect(() => {
        if (mode === "lobby") {
            navigate("/");
        }
    }, [mode, navigate]);

    return mode === "lobby" ? (
        <Bubble>
            <div className="d-flex">
                <Spinner animation="border" className="my-3 mx-auto" />
            </div>
        </Bubble>
    ) : (
        <>
            <Bubble>
                <Stack gap={2} className="">
                    <RoomHeader />
                    <hr className="my-0" />
                    <Rules />
                    <hr className="my-0" />
                    <ButtonBar />
                </Stack>
            </Bubble>
            <ScoreCard />
            {mode === "game" && (
                <>
                    <CurrentPlayer />
                    <WordList />
                </>
            )}
        </>
    );
}

function RoomHeader() {
    const { roomState: _roomState } = useStore();
    const roomState = _roomState as RoomState;

    const icons = [
        {
            symbol: roomState.status === "Closed" ? "lock" : "lock_open_right",
            tooltip:
                roomState?.status === "Closed"
                    ? "No new players can join the room"
                    : "Players can freely join the room",
            className: "ms-auto",
        },
        {
            symbol: "group",
            value: `${Object.keys(roomState.players).length}/${roomState.capacity}`,
            tooltip: "Number of players in the room",
        },
        {
            symbol: "manage_accounts",
            value: roomState.owner_name,
            tooltip: "Owner of the room",
        },
    ];

    return (
        <Stack direction="horizontal" gap={2} className="px-2">
            <div className="fs-4">{roomState.name}</div>
            {icons.map((icon, index) => (
                <React.Fragment key={index}>
                    {index !== 0 && <div className="vr" />}
                    <Icon {...icon} />
                </React.Fragment>
            ))}
        </Stack>
    );
}

function Rules() {
    const { roomState: _roomState } = useStore();
    const roomState = _roomState as RoomState;

    const icons = [
        {
            symbol: "skull",
            value: roomState.rules.type === "deathmatch" ? "Deathmatch" : "Error",
            tooltip: "Game type",
        },
        {
            symbol: "history",
            value: roomState.rules.round_time,
            tooltip: "Length of a round in seconds",
        },
        {
            symbol: "start",
            value: roomState.rules.start_score,
            tooltip: "Amount of points each players starts with",
        },
        {
            symbol: "check",
            value: roomState.rules.reward,
            tooltip: "Amount of points awarded for correct word",
        },
        {
            symbol: "dangerous",
            value: roomState.rules.penalty,
            tooltip: "Amount of points subtracted due to wrong answer",
        },
    ];

    return (
        <Stack direction="horizontal" gap={2} className="justify-content-evenly">
            {icons.map((icon, index) => (
                <React.Fragment key={index}>
                    {index !== 0 && <div className="vr" />}
                    <Icon {...icon} />
                </React.Fragment>
            ))}
        </Stack>
    );
}

function ButtonBar() {
    const {
        player: _player,
        roomState: _roomState,
        chatMessages,
        switchMode,
        updateChatMessages,
        purgeChatMessages,
        isRoomOwner,
        toggleModal,
        updateLobbyState,
        updateGameState,
        resetGameState,
    } = useStore();
    const player = _player as Player;
    const roomState = _roomState as RoomState;

    const navigate = useNavigate();

    async function handleLeaveRoom(roomId: number) {
        const prevMessages = [...chatMessages];
        purgeChatMessages();

        let response;
        try {
            response = await apiClient.post<LobbyState>(`/rooms/${roomId}/leave`);
        } catch (error) {
            updateChatMessages(prevMessages); // Restore chat messages in case `leave` request fails
            return;
        }
        updateLobbyState(response.body);
        switchMode("lobby");
        navigate("/");
    }

    async function toggleRoomStatus(roomId: number) {
        try {
            await apiClient.post(`/rooms/${roomId}/status`);
        } catch (error) {
            //TODO: Handle error
        }
    }

    async function toggleReady(roomId: number) {
        try {
            await apiClient.post(`/rooms/${roomId}/ready`);
        } catch (error) {
            //TODO: Handle error
        }
    }

    async function startGame(roomId: number) {
        let response;
        try {
            response = await apiClient.post<GameState>(`/rooms/${roomId}/start`);
        } catch (error) {
            //TODO: Handle error
            return;
        }
        resetGameState();
        updateGameState(response.body);
        switchMode("game");
    }

    return (
        <Stack gap={2} direction="horizontal">
            <Button
                variant="primary"
                size="sm"
                onClick={() => handleLeaveRoom(roomState?.id as number)}
                className="ms-auto"
            >
                Leave
            </Button>
            {isRoomOwner() ? (
                <>
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => toggleRoomStatus(roomState.id as number)}
                    >
                        {roomState.status === "Open" ? "Close" : "Open"}
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                            toggleModal("roomRules", {
                                disabledFields: ["name"],
                                defaultValues: {
                                    name: roomState.name,
                                    capacity: roomState.capacity,
                                    rules: {
                                        type: roomState.rules.type,
                                        penalty: roomState.rules.penalty,
                                        reward: roomState.rules.reward,
                                        start_score: roomState.rules.start_score,
                                        round_time: roomState.rules.round_time,
                                    },
                                },
                                onSubmit: "PUT",
                            });
                        }}
                    >
                        Rules
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        onClick={() => startGame(roomState.id as number)}
                        disabled={
                            !Object.values(roomState.players)
                                .filter((p) => p.name !== player.name)
                                .every((p) => p.ready)
                        }
                    >
                        Start
                    </Button>
                </>
            ) : (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => toggleReady(roomState.id as number)}
                >
                    {roomState.players[player.name].ready ? "Unready" : "Ready"}
                </Button>
            )}
        </Stack>
    );
}

function ScoreCard() {
    const { mode, roomState: _roomState, isRoomOwner } = useStore();
    const roomState = _roomState as RoomState;

    return (
        <Bubble>
            <Table borderless size="sm" className="m-0">
                <thead className="border-bottom">
                    <tr>
                        <td>
                            <Icon symbol="leaderboard" tooltip="Number" iconSize={4} />
                        </td>
                        <td>
                            <Icon symbol="person" tooltip="Name" iconSize={4} />
                        </td>
                        {mode === "game" ? (
                            <>
                                <td className="fw-bold">Points</td>
                                <td className="fw-bold">Mistakes</td>
                            </>
                        ) : (
                            <td>
                                <Icon symbol="light_mode" tooltip="Readiness" iconSize={4} />
                            </td>
                        )}
                    </tr>
                    <tr style={{ height: "0.25rem" }}></tr>
                </thead>
                <tbody>
                    <tr style={{ height: "0.25rem" }}></tr>
                    {(mode === "room" ? Object.values(roomState.players) : [])
                        // : (gameState as GameState).players
                        .map((player, index) => {
                            return (
                                <tr key={player.name}>
                                    <td>{index + 1}</td>
                                    <td>{player.name}</td>
                                    {mode === "game" ? (
                                        <>
                                            <td>{/* {gamePlayers[player.name].points} */}0</td>
                                            <td>{/* {gamePlayers[player.name].mistakes} */}0</td>
                                        </>
                                    ) : (
                                        <td>
                                            {isRoomOwner(player.name) ? (
                                                <Icon
                                                    symbol="manage_accounts"
                                                    tooltip="Owner"
                                                    iconSize={4}
                                                />
                                            ) : player.ready ? (
                                                <Icon
                                                    symbol="check"
                                                    className="text-success"
                                                    tooltip="Ready"
                                                    iconSize={4}
                                                />
                                            ) : (
                                                <Icon
                                                    symbol="close"
                                                    className="text-danger"
                                                    tooltip="Unready"
                                                    iconSize={4}
                                                />
                                            )}
                                        </td>
                                    )}
                                </tr>
                            );
                        })}
                </tbody>
            </Table>
        </Bubble>
    );
}

function CurrentPlayer() {
    const { gamePlayers: _gamePlayers, gameCurrentTurn: _gameCurrentTurn } = useStore();
    const gamePlayers = _gamePlayers as GamePlayer[];
    const gameCurrentTurn = _gameCurrentTurn as Turn;

    let players;
    if (gamePlayers.length < 3) {
        players = gamePlayers;
    } else {
        const prevIndex = (gameCurrentTurn.current_player_idx - 1) % gamePlayers.length;
        const nextIndex = (gameCurrentTurn.current_player_idx + 1) % gamePlayers.length;
        players = [
            // Find the previous, current and next player to be render in the bubble
            gamePlayers[prevIndex < 0 ? prevIndex + gamePlayers.length : prevIndex],
            gamePlayers[gameCurrentTurn.current_player_idx],
            gamePlayers[nextIndex],
        ];
    }

    return (
        <Bubble>
            <Stack direction="horizontal" gap={2} className="justify-content-evenly">
                {Object.values(players).map((player, index) => {
                    return (
                        <>
                            {index !== 0 && <Icon symbol="trending_flat" iconSize={3} />}
                            {index === 1 ? (
                                <Stack key={player.name} direction="horizontal" gap={2}>
                                    <Icon symbol="arrow_forward_ios" iconSize={5} />
                                    <div className="fs-5">{player.name}</div>
                                    <Icon symbol="arrow_back_ios" iconSize={5} />
                                </Stack>
                            ) : (
                                <div className="fs-6" key={player.name}>
                                    {player.name}
                                </div>
                            )}
                        </>
                    );
                })}
            </Stack>
        </Bubble>
    );
}

function WordList() {
    const { roomState, gamePlayers: _gamePlayers, gameTurns: _gameTurns } = useStore();
    const gamePlayers = _gamePlayers as GamePlayer[];
    const gameTurns = _gameTurns as Turn[];

    const turns = gameTurns.length > 5 ? gameTurns.slice(-5) : gameTurns;

    const positionToSize: Record<number, string> = {
        0: "fs-6",
        1: "fs-5",
        2: "fs-4",
        3: "fs-3",
        4: "fs-2",
        5: "fs-1",
    };
    const symbol = (word: Word) => (word.is_correct ? "check" : "close");
    const points = (word: Word) =>
        word.is_correct ? "+" + roomState?.rules.reward : roomState?.rules.penalty;
    const color = (word: Word) => (word.is_correct ? "text-success" : "text-danger"); // GREEN or RED

    const style = {
        flexGrow: 1,
        flexShrink: 0,
        justifyContent: "center",
        alignItems: "center",
    };

    return (
        <Bubble>
            <Table borderless className="m-0 text-center">
                <tbody>
                    {Array.from({ length: 5 }).map((_, index) => {
                        const turnOffset = 5 - turns.length;
                        const turnIndex = index - turnOffset;
                        if (turnIndex < 0) {
                            return;
                        }

                        const word = turns[turnIndex].word as Word;
                        const player_name = gamePlayers[turns[turnIndex].current_player_idx].name;
                        console.log("turnIndex", turnIndex);
                        console.log("index", index);
                        console.log("turnOffset", turnOffset);
                        return (
                            <tr
                                style={style}
                                className="d-flex justify-content-between"
                                key={word.content}
                            >
                                <td style={{ flexBasis: "20%" }} className="p-0 border-0">
                                    {player_name}
                                </td>
                                <td className="p-0 border-0">
                                    <Stack direction="horizontal" gap={2}>
                                        <div
                                            style={{ flexBasis: "60%" }}
                                            className={`p-0 border-0 ${positionToSize[index]}`}
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
                                className="py-1 mt-1 w-50"
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
        </Bubble>
    );
}
