import React, { useEffect, useRef } from "react";
import { Button, Spinner, Stack } from "react-bootstrap";
import { Container } from "react-bootstrap";
import Form from "react-bootstrap/Form";
import Table from "react-bootstrap/Table";
import { useNavigate } from "react-router-dom";

import apiClient from "../apiClient";
import Bubble from "../components/Bubble";
import CountdownTimer from "../components/CountdownTimer";
import Icon from "../components/Icon";
import IconBar from "../components/IconBar";
import { WORD_LIST_LENGTH, WORD_LIST_MAX_WORD_SIZE } from "../config";
import { useStore } from "../contexts/storeContext";
import { useWebSocketContext } from "../contexts/WebsocketProvider";
import { DeathmatchRules, GamePlayer, LobbyState, Player, RoomState, Turn, Word } from "../types";

export default function RoomPage() {
    const { mode, gameState } = useStore();

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
            {mode === "room" && <PlayerList />}
            {mode === "game" && (
                <>
                    <ScoreCard />
                    {gameState !== "ENDED" ? (
                        <>
                            <CurrentPlayer />
                            <WordList />
                        </>
                    ) : (
                        <WordSummary />
                    )}
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

    const elements = [
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

    return <IconBar elements={elements} />;
}

function ButtonBar() {
    const {
        loggedPlayer: _player,
        roomState: _roomState,
        chatMessages,
        switchMode,
        updateChatMessages,
        purgeChatMessages,
        isRoomOwner,
        toggleModal,
        updateLobbyState,
        mode,
        gameState,
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

    async function returnToRoom(roomId: number) {
        try {
            await apiClient.post<null>(`/rooms/${roomId}/return`);
        } catch (error) {
            //TODO: Handle error
            return;
        }
        switchMode("room");
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
            {mode === "room" &&
                (isRoomOwner() ? (
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
                        hidden={roomState.status === "In progress"}
                    >
                        {roomState.players[player.name].ready ? "Unready" : "Ready"}
                    </Button>
                ))}
            {mode === "game" && gameState === "ENDED" && (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => returnToRoom(roomState.id!)}
                    disabled={roomState.status === "In progress"}
                >
                    Return to room
                </Button>
            )}
        </Stack>
    );
}

function PlayerList() {
    const { roomState: _roomState, isRoomOwner, loggedPlayer } = useStore();
    const roomState = _roomState as RoomState;

    function mutePlayer(playerName: string) {}

    function kickPlayer(playerName: string) {
        try {
            apiClient.post(`/rooms/${roomState.id}/players/${playerName}/kick`);
        } catch (error) {
            //TODO: Handle error
            return;
        }
    }

    return (
        <Bubble>
            <Table borderless size="sm" className="m-0">
                <thead className="border-bottom">
                    <tr>
                        <td>
                            <Icon symbol="person" tooltip="Name" iconSize={4} />
                        </td>
                        <td>
                            <Icon
                                symbol="hand_gesture"
                                tooltip="Player returned from the previous game"
                                iconSize={4}
                            />
                        </td>
                        <td>
                            <Icon symbol="light_mode" tooltip="Readiness" iconSize={4} />
                        </td>
                    </tr>
                    <tr style={{ height: "0.5rem" }} />
                </thead>

                <tbody>
                    <tr style={{ height: "0.5rem" }} />
                    {Object.values(roomState.players).map((roomPlayer, index) => {
                        return (
                            <tr key={roomPlayer.name}>
                                <td>{roomPlayer.name}</td>
                                <td>
                                    {roomPlayer.in_game ? (
                                        <Icon
                                            symbol="close"
                                            className="text-danger"
                                            tooltip="Not available"
                                            iconSize={4}
                                        />
                                    ) : (
                                        <Icon
                                            symbol="check"
                                            className="text-success"
                                            tooltip="Available"
                                            iconSize={4}
                                        />
                                    )}
                                </td>
                                <td>
                                    {isRoomOwner(roomPlayer.name) ? (
                                        <Icon
                                            symbol="manage_accounts"
                                            tooltip="Owner"
                                            iconSize={4}
                                        />
                                    ) : roomPlayer.ready ? (
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
                                <td>
                                    <Stack
                                        direction="horizontal"
                                        gap={2}
                                        className="justify-content-end"
                                    >
                                        {roomPlayer.name != loggedPlayer?.name && (
                                            <Button
                                                onClick={() => {
                                                    mutePlayer(roomPlayer.name);
                                                }}
                                                variant="primary"
                                                size="sm"
                                                disabled
                                            >
                                                Mute
                                            </Button>
                                        )}
                                        {isRoomOwner() && roomPlayer.name != loggedPlayer?.name && (
                                            <Button
                                                onClick={() => {
                                                    kickPlayer(roomPlayer.name);
                                                }}
                                                variant="primary"
                                                size="sm"
                                            >
                                                Kick
                                            </Button>
                                        )}
                                    </Stack>
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
                    <tr style={{ height: "0.5rem" }} />
                </thead>
                <tbody>
                    <tr style={{ height: "0.5rem" }} />
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
                                    <td>{player.place ? player.place : index + 1}</td>
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
    const { gamePlayers, currentTurn, gameRules, gameState } = useStore() as {
        gamePlayers: GamePlayer[];
        currentTurn: Turn;
        gameRules: DeathmatchRules;
        gameState: "STARTED" | "ENDED" | "WAITING" | "STARTED_TURN" | "ENDED_TURN";
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

            <Container
                className="d-flex justify-content-evenly align-items-center"
                style={{ height: "35px" }}
            >
                {gameState === "STARTED" ? (
                    <Spinner animation="border" size="sm" />
                ) : gameState === "WAITING" ? (
                    <Spinner animation="border" size="sm" />
                ) : (
                    <CountdownTimer
                        time={gameRules.round_time}
                        start_date={currentTurn.started_on}
                        precisionDigit={2}
                        className="fs-4"
                    />
                )}
            </Container>
        </Bubble>
    );
}

function WordList() {
    const {
        roomState,
        gamePlayers: _gamePlayers,
        gameTurns: _gameTurns,
        isLoggedPlayersTurn: isLocalPlayersTurn,
        currentTurn: _currentTurn,
        gameState: _gameState,
    } = useStore();
    const gamePlayers = _gamePlayers as GamePlayer[];
    const gameTurns = _gameTurns as Turn[];
    const currentTurn = _currentTurn as Turn;
    const gameState = _gameState as "STARTED" | "ENDED" | "WAITING" | "STARTED_TURN" | "ENDED_TURN";

    const { sendWordInput } = useWebSocketContext();
    const wordRef = useRef<HTMLInputElement>(null);

    function submitNewWord(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const word = wordRef.current?.value;
        if (!word) {
            return;
        }
        sendWordInput(word);
        wordRef.current!.value = "";
    }

    let positionToSize: Record<number, { fontSize: string }> = {};
    const sizeStep = WORD_LIST_MAX_WORD_SIZE / WORD_LIST_LENGTH;
    for (let i = 0; i <= WORD_LIST_LENGTH; i++) {
        positionToSize[i] = { fontSize: `${(i + 1) * sizeStep}rem` };
    }

    const symbol = (word: Word) => (word.is_correct ? "check" : "close");
    const points = (word: Word | null) =>
        word?.is_correct ? "+" + roomState?.rules.reward : roomState?.rules.penalty;
    const color = (word: Word | null) => (word?.is_correct ? "text-success" : "text-danger"); // GREEN or RED
    const tooltip = (turn: Turn) => {
        if (turn.word?.is_correct) {
            let tooltipText = "";
            turn.word.description!.forEach(([partOfSpeech, description]) => {
                tooltipText += `${partOfSpeech}: ${description}\n\n`;
            });
            return tooltipText;
        } else {
            return turn.info as string;
        }
    };

    return (
        <Bubble>
            <Container className="px-2 py-1">
                <Table borderless className="m-0 text-center">
                    <tbody>
                        {Array.from({ length: WORD_LIST_LENGTH }).map((_, index) => {
                            const turnOffset = WORD_LIST_LENGTH - gameTurns.length;
                            const turnIndex: number = index - turnOffset;
                            if (turnIndex < 0) {
                                return;
                            }

                            const gameTurn = gameTurns[turnIndex];
                            const word = gameTurn.word;
                            const player_name = gamePlayers[gameTurn.player_idx].name;
                            return (
                                <tr key={word ? word.content : index}>
                                    <td
                                        className="p-0 border-0 align-middle"
                                        style={{ height: "35px" }}
                                    >
                                        {player_name}
                                    </td>
                                    <td
                                        className="d-flex p-0 border-0 justify-content-center align-middle"
                                        style={{ height: "35px" }}
                                    >
                                        <Stack direction="horizontal" gap={3}>
                                            <div
                                                className={`p-0 border-0`}
                                                style={positionToSize[index]}
                                            >
                                                {word ? word.content : "-"}
                                            </div>
                                            <div>
                                                {word && (
                                                    <Icon
                                                        symbol={symbol(word)}
                                                        color={color(word)}
                                                        tooltip={tooltip(gameTurn)}
                                                        iconSize={3}
                                                    />
                                                )}
                                            </div>
                                        </Stack>
                                    </td>
                                    <td
                                        className={`p-0 border-0 align-middle ${color(word)}`}
                                        style={{ height: "35px" }}
                                    >
                                        {points(word)}
                                    </td>
                                </tr>
                            );
                        })}
                        <tr>
                            <td className="p-0 border-0 align-middle" style={{ height: "35px" }}>
                                {["STARTED_TURN", "ENDED_TURN"].includes(gameState)
                                    ? gamePlayers[currentTurn?.player_idx as number].name
                                    : gamePlayers[0].name}
                            </td>
                            {gameState === "STARTED_TURN" && isLocalPlayersTurn() ? (
                                <td
                                    className={`d-flex p-0 m-1 border-0 ${positionToSize[5]} justify-content-center`}
                                    style={{ height: "35px" }}
                                >
                                    <Form
                                        onSubmit={submitNewWord}
                                        className="d-flex justify-content-center w-100"
                                    >
                                        <Form.Control
                                            type="text"
                                            placeholder="Write here..."
                                            className="p-0"
                                            ref={wordRef}
                                            autoFocus
                                            style={{
                                                textAlign: "center",
                                                border: "none",
                                                outline: "none",
                                                boxShadow: "none",
                                            }}
                                        />
                                    </Form>
                                </td>
                            ) : (
                                <td
                                    className={`d-flex p-0 m-1 border-0 align-items-center justify-content-center`}
                                    style={{ height: "35px" }}
                                >
                                    <Spinner animation="border" size="sm" className="m-auto" />
                                </td>
                            )}
                            <td></td>
                        </tr>
                    </tbody>
                </Table>
            </Container>
        </Bubble>
    );
}

function WordSummary() {
    const { roomState, gamePlayers: _gamePlayers, gameTurns: _gameTurns } = useStore();
    const gamePlayers = _gamePlayers as GamePlayer[];
    const gameTurns = _gameTurns as Turn[];

    const symbol = (word: Word) => (word.is_correct ? "check" : "close");
    const points = (word: Word | null) =>
        word?.is_correct ? "+" + roomState?.rules.reward : roomState?.rules.penalty;
    const color = (word: Word | null) => (word?.is_correct ? "text-success" : "text-danger"); // GREEN or RED
    const tooltip = (turn: Turn) => {
        if (turn.word?.is_correct) {
            let tooltipText = "";
            turn.word.description!.forEach(([partOfSpeech, description]) => {
                tooltipText += `${partOfSpeech}: ${description}\n\n`;
            });
            return tooltipText;
        } else {
            return turn.info as string;
        }
    };

    return (
        <Bubble>
            <Container
                className="px-2 p-0"
                style={{
                    maxHeight: `${WORD_LIST_LENGTH * 35}px`,
                    overflowY: "auto",
                }}
            >
                <Table borderless className="m-0 text-center">
                    <tbody>
                        {gameTurns.map((gameTurn, index) => {
                            const word = gameTurn.word;
                            const player_name = gamePlayers[gameTurn.player_idx].name;
                            return (
                                <tr key={index}>
                                    <td
                                        className="p-0 border-0 align-middle"
                                        style={{ height: "35px" }}
                                    >
                                        {player_name}
                                    </td>
                                    <td
                                        className="d-flex p-0 border-0 justify-content-center align-middle"
                                        style={{ height: "35px" }}
                                    >
                                        <Stack direction="horizontal" gap={3}>
                                            <div className={`p-0 border-0`}>
                                                {word ? word.content : "-"}
                                            </div>
                                            <div>
                                                {word && (
                                                    <Icon
                                                        symbol={symbol(word)}
                                                        color={color(word)}
                                                        tooltip={tooltip(gameTurn)}
                                                        iconSize={3}
                                                    />
                                                )}
                                            </div>
                                        </Stack>
                                    </td>
                                    <td
                                        className={`p-0 border-0 align-middle ${color(word)}`}
                                        style={{ height: "35px" }}
                                    >
                                        {points(word)}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </Table>
            </Container>
        </Bubble>
    );
}
