import React, { useEffect, useRef } from "react";
import { Button, Spinner, Stack } from "react-bootstrap";
import Form from "react-bootstrap/Form";
import Table from "react-bootstrap/Table";
import { useNavigate } from "react-router-dom";

import apiClient from "../apiClient";
import Bubble from "../components/Bubble";
import CountdownTimer from "../components/CountdownTimer";
import Icon from "../components/Icon";
import { useStore } from "../contexts/storeContext";
import { useWebSocketContext } from "../contexts/WebsocketProvider";
import { DeathmatchRules, GamePlayer, LobbyState, Player, RoomState, Turn, Word } from "../types";

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
            {mode === "room" ? (
                <PlayerCard />
            ) : (
                <>
                    <ScoreCard />
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
            symbol:
                roomState?.status === "Closed"
                    ? "lock"
                    : roomState?.status === "In progress"
                    ? "clock_loader_40"
                    : "lock_open_right",
            tooltip:
                roomState?.status === "Closed"
                    ? "No new players can join the room"
                    : roomState?.status === "In progress"
                    ? "Game in progress"
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
        <Stack direction="horizontal" gap={3} className="px-2">
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
        try {
            await apiClient.post<null>(`/rooms/${roomId}/start`);
        } catch (error) {
            //TODO: Handle error
            return;
        }
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
                        disabled={roomState.status === "In progress"}
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
                        disabled={roomState.status === "In progress"}
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
                                .every((p) => p.ready) || roomState.status === "In progress"
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
                    disabled={roomState.status === "In progress"}
                >
                    {roomState.players[player.name].ready ? "Unready" : "Ready"}
                </Button>
            )}
        </Stack>
    );
}

function PlayerCard() {
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
                        <td>
                            <Icon symbol="light_mode" tooltip="Readiness" iconSize={4} />
                        </td>
                    </tr>
                    <tr style={{ height: "0.25rem" }} />
                </thead>

                <tbody>
                    <tr style={{ height: "0.25rem" }} />
                    {Object.values(roomState.players).map((player, index) => {
                        return (
                            <tr key={player.name}>
                                <td>{index + 1}</td>
                                <td>{player.name}</td>

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
                            </tr>
                        );
                    })}
                </tbody>
            </Table>
        </Bubble>
    );
}

function ScoreCard() {
    const { gamePlayers: _gamePlayers } = useStore();
    const gamePlayers = _gamePlayers as GamePlayer[];

    return (
        <Bubble>
            <Table borderless size="sm" className="m-0">
                <thead className="border-bottom">
                    <tr>
                        <td>
                            <Icon symbol="leaderboard" tooltip="Position" iconSize={4} />
                        </td>
                        <td>
                            <Icon symbol="person" tooltip="Name" iconSize={4} />
                        </td>
                        <td>
                            <Icon symbol="scoreboard" tooltip="Score" iconSize={4} />
                        </td>
                        <td>
                            <Icon symbol="error" tooltip="Mistakes" iconSize={4} />
                        </td>
                    </tr>
                    <tr style={{ height: "0.25rem" }} />
                </thead>
                <tbody>
                    <tr style={{ height: "0.25rem" }} />
                    {[...gamePlayers]
                        .sort((a, b) => {
                            if (a.place !== null && b.place !== null) {
                                // If both places are not null, sort by place
                                return a.place - b.place;
                            } else if (a.place !== null) {
                                // If only a's place is not null, b comes first
                                return 1;
                            } else if (b.place !== null) {
                                // If only b's place is not null, a comes first
                                return -1;
                            } else {
                                // If both places are null, sort by score
                                return a.score - b.score;
                            }
                        })
                        .map((player, index) => {
                            return (
                                <tr key={player.name}>
                                    <td>{player.place ? player.place : "-"}</td>
                                    <td>{player.name}</td>

                                    <td>{player.score}</td>
                                    <td>{player.mistakes}</td>
                                </tr>
                            );
                        })}
                </tbody>
            </Table>
        </Bubble>
    );
}

function CurrentPlayer() {
    const { gamePlayers, currentTurn, gameStatus, gameRules } = useStore() as {
        gamePlayers: GamePlayer[];
        currentTurn: Turn;
        gameStatus: string;
        gameRules: DeathmatchRules;
    };

    let players;
    if (gamePlayers.length < 3) {
        players = gamePlayers;
    } else {
        const prevIndex = (currentTurn.player_idx - 1) % gamePlayers.length;
        const nextIndex = (currentTurn.player_idx + 1) % gamePlayers.length;
        players = [
            // Find the previous, current and next player to be render in the bubble
            gamePlayers[prevIndex < 0 ? prevIndex + gamePlayers.length : prevIndex],
            gamePlayers[currentTurn.player_idx],
            gamePlayers[nextIndex],
        ];
    }

    return (
        <Bubble>
            <Stack direction="horizontal" gap={2} className="justify-content-evenly">
                {Object.values(players).map((player, index) => {
                    return (
                        <React.Fragment key={player.name}>
                            {index !== 0 && <Icon symbol="trending_flat" iconSize={3} />}
                            {(players.length >= 3 && index === 1) ||
                            (players.length < 3 && index === 0) ? (
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
                        </React.Fragment>
                    );
                })}
            </Stack>

            <Stack direction="horizontal" gap={2} className="fs-4 justify-content-evenly">
                {gameStatus === "In progress" ? (
                    <CountdownTimer
                        time={gameRules.round_time}
                        start_date={currentTurn.started_on}
                        precisionDigit={2}
                    />
                ) : (
                    <CountdownTimer time={3} precisionDigit={0} />
                )}
            </Stack>
        </Bubble>
    );
}

function WordList() {
    const {
        roomState,
        gamePlayers: _gamePlayers,
        gameTurns: _gameTurns,
        isLocalPlayersTurn,
        currentTurn,
        gameStatus: _gameStatus,
    } = useStore();
    const gamePlayers = _gamePlayers as GamePlayer[];
    const gameTurns = _gameTurns as Turn[];
    const gameStatus = _gameStatus as string;

    const { sendWordInput } = useWebSocketContext();

    const turns = gameTurns.length > 5 ? gameTurns.slice(-5) : gameTurns;
    const wordRef = useRef<HTMLInputElement>(null);

    function submitNewWord(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const word = wordRef.current?.value;
        if (!word) {
            return;
        }
        sendWordInput(word);
    }

    const positionToSize: Record<number, string> = {
        0: "fs-6",
        1: "fs-5",
        2: "fs-4",
        3: "fs-3",
        4: "fs-2",
        5: "fs-1",
    };
    const symbol = (word: Word) => (word.is_correct ? "check" : "close");
    const points = (word: Word | null) =>
        word?.is_correct ? "+" + roomState?.rules.reward : roomState?.rules.penalty;
    const color = (word: Word | null) => (word?.is_correct ? "text-success" : "text-danger"); // GREEN or RED

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
                        const turnIndex: number = index - turnOffset;
                        if (turnIndex < 0) {
                            return;
                        }

                        const word = turns[turnIndex].word;
                        const player_name = gamePlayers[turns[turnIndex].player_idx].name;

                        return (
                            <tr
                                style={style}
                                className="d-flex justify-content-between"
                                key={word ? word.content : index}
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
                                            {word ? word.content : "-"}
                                        </div>
                                        <div
                                            style={{ flexBasis: "10%" }}
                                            className={`p-0 border-0 material-symbols-outlined ${color(
                                                word
                                            )}`}
                                        >
                                            {word ? symbol(word) : ""}
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
                            {gameStatus === "In progress"
                                ? gamePlayers[currentTurn?.player_idx as number].name
                                : gamePlayers[0].name}
                        </td>
                        {isLocalPlayersTurn() ? (
                            <td
                                style={{ flexBasis: "60%" }}
                                className={`d-flex p-0 border-0 ${positionToSize[5]} justify-content-center`}
                            >
                                <Form onSubmit={submitNewWord}>
                                    <Form.Control
                                        type="text"
                                        placeholder="Write here..."
                                        className="py-1 mt-1 w-50"
                                        disabled={gameStatus !== "In progress"}
                                        ref={wordRef}
                                    />
                                </Form>
                            </td>
                        ) : (
                            <td
                                style={{ flexBasis: "60%" }}
                                className={`d-flex p-0 border-0 justify-content-center`}
                            >
                                <Spinner animation="border" size="sm" className="my-2 mx-auto" />
                            </td>
                        )}
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
