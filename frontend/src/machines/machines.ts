import { createMachine, assign } from 'xstate';
import { Player, LobbyState, RoomState, GameState } from '@/types';

type StateEvent<T> = {
    type: string;
    data: T;
}

/** @xstate-layout N4IgpgJg5mDOIC5QEMAOqB0AZA9lGEA8gK4AuAxAMYBOYypYACgDbICeY1A2gAwC6iUKhywAlqVE4AdoJAAPRAFoAzAA4AbBgDs6gKzqATLoA0INkoCMBgwF8bptJlz5IJCszwBJKbwFIQwmIS0rIKCIq6FjwYPFqqViZmltZ2DujYOABGmWzkHlBuvrKB4pIy-mGKBgAsFhgGFqpaiebhVrb2II4Z2bkAVjiiUgBKODgAtkX+JcHloJXV6pqx8UamrQYAnKld6aMTeXQAbmD7k-zFIqUhFUoGGhi6cQnriFs73WfksKTI1KQAcWQ4zAUyEV1moSUyi0m0eukWTRab1ijzsnSkOAgcFkjkuQTKUPCul0qhizzWSXCWx4H3SzgIbnx1zm8mhsIwS2qPEMyOpPGUaM63VwvWZkNu4RhdSeqz5imqHTSmDO4sJkpUWhlFL5FisdMwQJBapu8yUtThspeVOUPF06JsQA */
export const machine = createMachine({
    /** @xstate-layout N4IgpgJg5mDOIC5QEMAOqB0AZA9lGEA8gK4AuAxBDgHZgYCW1AbjgNZ1qa76QmkKMWAY2Sl6NANoAGALrSZiUKhyx6YmopAAPRAEYATAE4MU-fqkBmM7oBshmwBYb+gDQgAnogC0Adl0YLewAOQwcgh10AVkiHJwBfOLdObDwCPnIwACdMnEyMVAAbUQAzXIBbDGTuNLIBZhwRdWp5eU1lVSbNHQQjHwwbG0ipKQdI-R9DUIsfN08EX39AmxCwiOjYmwSk9BSeIjJKGjpBNg4d6t5ak8bxZt05WTaVNVuuxCDwjCCbH0cjXUsUiCMw83gGAV0PnGoSkkRC4y2ICqqUuFCyOTyhRK5Uq5xR+3411Etwk91aSBA7ReGgp3UGUgwuhCPj8sV0uicQVm3j8AWCwKkhikyyCFiCiORACNJe5DrQGPV2LiuDhpe46sJiZJZOSlM9OrS9GYMCzDOEPutQvoHNyELpDPoMGZRYYfKLxvpvhK8WqMtlcvkiqRSpkKlKZRqGlrmjrHhSqQbQN1PZEnSNYRZIUyzYZbfaHCYIlJdBZooZ8z5vSrfQU8HxdZT9a9DQgHK6nfobKZIl3O2Me7bfI6QiL2WbO79dFWMAAlHA4MrkApgZBMMBzhcNhPNpOIPyOnwOQVQ2IWLslvNCk2esVBe1jBz6EvTjeL2CkZCZUgAcWQZTAW5NjSu4IFYjoOCyFqPiMd4gnMYT+HeFhAnYdi2GaFjTr+-7kAAomu1CkAABLogEdDu2iIAMqY9nYwpikYtoIV8JYofY5Z2KKWF-nQADumRqGAADquQQOQsBgNQEAiZkEBkdS1BvK2cJOpE5b2ECT7AjYtpQv4QIfOEpaGP2hjcf+GAFPQ76SQAKjgMkQLAeEEcRpFxnq5HAZRrb6KmmZiuW9rTD4Yy2kEIwmKYQRmGaanmJsiLUDgEBwJonBPF5iktoeJoTOaQSWo+NqgvMmaOmewoaZ6dEctOFwEplClKRsGCPuWh7OGYsJwd4ZgFt8Ug+MMXbTJEpZTokSI+jKTWJj5ow2Bg42FbCETLLYpa2ipTgQT27J3pEkIvvOZRzRR3Rtv4USRMNmZHa6BglXMFiBIyg22G6oSPn55lgOd3nJiy-Rtm6xYrbEz1UVYAS3mNoSGMhZlTck2F8QJpDCaJAPZSBVipo4roRVEYqQ7p9pfLejimK9ViYSjOxo5Z1mY9Q9mOfA8ZAbjPk2EyXwabdPawuN5PGKKHwmaYPyuvoCQJEAA */
    id: "app",
    schemas: {
        services: {} as {
            logIn: { data: Player };
            createPlayer: { data: Player };
        }
    },
    states: {
        LoggedOut: {
            invoke: [
                {
                    src: "logIn",
                    onDone: {
                        target: "Lobby",
                        actions: "assignPlayer"
                    },
                    onError: {
                        target: "LoggedOut",
                        actions: "assignLogInErrors"
                    }
                }
                ,
                {
                    src: "createPlayer",
                    onDone: {
                        target: "Lobby",
                        actions: "assignPlayer"
                    },
                    onError: {
                        target: "LoggedOut",
                        actions: "assignCreatePlayerErrors"
                    }
                }]
        },

        Lobby: {
            invoke: {
                src: "joinRoom",
                onDone: {
                    target: "Room"
                },
                onError: {
                    target: "Lobby",
                    actions: "assignJoinRoomErrors"
                }
            },
            on: {
                logOut: "LoggedOut"
            }
        },

        Room: {
            on: {
                leaveRoom: "Lobby",
                startGame: "Game"
            }
        },

        Game: {
            states: {
                writeWord: {
                    on: {
                        sendWord: "listenToWords"
                    }
                },

                listenToWords: {
                    on: {
                        "Event 1": {
                            target: "writeWord",
                            guard: "isMyTurn"
                        }
                    }
                }
            },

            initial: "writeWord",

            on: {
                "Event 1": "Room"
            }
        }
    },
    initial: "LoggedOut",
    context: {
        player: null as Player | null,
        errors: [] as string[],
        gameState: null as GameState | null,
        roomState: null as RoomState | null,
        lobbyState: null as LobbyState | null
    }
},
    {
        actions: {
            assignPlayer: assign((context, event) => {
                return {
                    player: (event as StateEvent<Player>).data
                }
            }),
            assignCreatePlayerErrors: assign((context, event) => {
                return {
                    errors: (event as StateEvent<string[]>).data
                }
            })
        },
    })