import { fromPromise, assign, createActor, setup } from 'xstate';
import { Player, LobbyState, RoomState, GameState } from '@/types';
import { UUID } from 'crypto';
import apiClient from "../apiClient";
import { RoomIn } from '../types';

type StateEventSuccess<T> = {
    type: string;
    output: T;
}

type StateEventError = {
    type: string;
    error: ErrorMessage;
}

type ErrorMessage = {
    type:
    | 'requestLogIn'
    | 'requestLogOut'
    | 'requestCreatePlayer'
    | 'requestJoinRoom'
    | 'requestCreateRoom'
    | 'requestLeaveRoom'
    | null;
    messages: string[];
}

export async function logIn({ input: { playerId } }: { input: { playerId: UUID } }): Promise<Player> {
    return apiClient.post<Player>("/players/login", { body: { id: playerId } })
        .then(response => response.body);
}

export async function logOut({ input: { playerId } }: { input: { playerId: UUID } }): Promise<Player> {
    return apiClient.post<Player>("/players/logout", { body: { id: playerId } })
        .then(response => response.body);
}

export async function createPlayer({ input: { playerName } }: { input: { playerName: string } }): Promise<Player> {
    return apiClient.post<Player>("/players", { body: { name: playerName } })
        .then(response => response.body);
}

export async function joinRoom({ input: { roomId } }: { input: { roomId: number } }): Promise<Player> {
    return apiClient.post<Player>(`/rooms/login/${roomId}/join`)
        .then(response => response.body);
}

export async function createRoom({ input }: { input: RoomIn }): Promise<Player> {
    return apiClient.post<Player>("/players", { body: input })
        .then(response => response.body);
}

/** @xstate-layout N4IgpgJg5mDOIC5QEMAOqB0AZA9lGEA8gK4AuAxBDgHZgYCW1AbjgNZ1qa76QmkKMWAY2Sl6NANoAGALrSZiUKhyx6YmopAAPRAFoALAA4AbBgCshgJxmAzPrPHj+ywHZDAGhABPPfoCMfhjGUjZSLgBM4dZ+-uEAvnGenNh4BHzkYABOmTiZGKgANqIAZrkAthjJ3GlkAsw4IurU8vKayqpNmjoIujZ+hhjW4X3hZvohTpaePj3j+hgm4SbGfis2biYJSegpPERklDR0gmwcO9W8tSeN4s1+crJtKmq3XYj6Rhgu-n5RflLhKT+Qz6aZ6GyGMyDVyWcIuPyWGyWWFArYgKqpS4ULI5PKFErlSrnTH7fjXUS3CT3VpIEDtF4aWndfrzJyGBH-FxjfROMGzIELYxLRyrPzrKxojF7dIAUSYYGopAABNRkGUwDSlM9Oky9MNTPCrFZHCYpEK+boxjZBr9EUD1rZ9DZJcSAEauryHWgMersIlcHDurx1YQUySyTV07WvXU9ULhL5SELOKJmFyWIwuPlSDBIgFhHmGEz9AGWF0BoMZbK5fJFUilTIVDFBkMNMPNCOPWn0nWgZlRDCjALGQzhPxpqRii1O3P-cLGGxpj5miLllKVgp4PiRnsxvt6wKAyxFqSjiLrY8WmxOL7-PpFxyIlxrgBKOBwZXIBTAyHlb4-O7Roy+4IDYcKDPoEQjg6Pygt4eiBAEYohCE4ROhYLiook6I7P+n6wKQyCZKQADiaoal2WodHu2gIcYLgLCY3xmkCx6cnyYHWt8C5jGYx7MYYa5keq5Bygqyp+IB1HAbRCBIQsbjWEmIxWG4fJRAxPJ8bYYqjh8dhCeRGAAO6ZGoYAAOq5BA5CwAqEBWZkEBSQy1BvAg-iDJh8I8qM15hH4fLBIh6xCi4xiuPaZbYckwl0AU9AEQqAAqOCORAsCifKipKpJlFRtJbmxo4GD2NemFmGmrjpnylXWmK4VwhFmFOtF2HUDgEBwJonBPIV7mWnY5hWI6DiTGp8E9I4DFWDEKYQhYaZrhcpJ9a5A0RIKYrIpY9ELqsFoWDmPLniCiKQoYzoxW6Hprb2sm6EKXxmJOljDsesTGBakSmGYkSrA4cyGKexivu+ZR3TR3S6AiuZ9L8XIuDYYHfOEfL9Amf0VRmZjjlEwyGeqkMydDwyBAuhjpi4mHrOMJh8lpt6LvoowvQE15XdsmBxSZZmkJZ1nE0VIEw5dQQQlTNMCV9k3BRgDVhc1UWE-FiX89QqXpfA3ZAcLD39NaFOSyE0t8kjUIrC9DhisjBPXQG+CMFAACSeu7iT4LWKVzhOEs4VJt8h0fBgk6TJVlhJh8ZgJAkQA */
const appMachine = setup({
    types: {
        context: {} as {
            player: Player | null,
            error: ErrorMessage,
            gameState: GameState | null,
            roomState: RoomState | null,
            lobbyState: LobbyState | null
        },
        events: {} as
            | { type: 'requestLogIn', playerId: UUID }
            | { type: 'requestCreatePlayer', playerName: string }
            | { type: 'requestLogOut' }
            | { type: 'requestJoinRoom', roomId: number }
            | { type: 'requestCreateRoom', roomIn: RoomIn }
            | { type: 'requestLeaveRoom' }
    },
    actors: {
        logIn: fromPromise(logIn),
        logOut: fromPromise(logOut),
        createPlayer: fromPromise(createPlayer),
        joinRoom: fromPromise(joinRoom),
        createRoom: fromPromise(createRoom),
    },
    actions: {
        assignPlayer: assign(({ context, event }) => {
            return {
                player: (event as StateEventSuccess<Player>).output
            }
        }),
        deassignPlayer: assign(({ context, event }) => {
            return { player: null }
        }),
        assignLogInErrors: assign(({ context, event }) => {
            return {
                error: {
                    type: 'requestLogIn' as 'requestLogIn',
                    messages: (event as StateEventError).error.messages
                }
            }
        }),
        assignCreatePlayerErrors: assign(({ context, event }) => {
            return {
                error: {
                    type: 'requestCreatePlayer' as 'requestCreatePlayer',
                    messages: (event as StateEventError).error.messages
                }
            }
        }),
        assignCreateRoomErrors: assign(({ context, event }) => {
            return {
                error: {
                    type: 'requestCreateRoom' as 'requestCreateRoom',
                    messages: (event as StateEventError).error.messages
                }
            }
        }),
        resetErrorMessages: assign(({ context, event }) => {
            return { error: { type: null, messages: [] } }
        }),
    },
}).createMachine({
    /** @xstate-layout N4IgpgJg5mDOIC5QEMAOqB0AZA9lGEA8gK4AuAxAE5gCOxcpAwtcqWAAoA2yAnmJQG0ADAF1EoVDlgBLUtJwA7cSAAeiAIwBOAMwYA7ABYAbOr16AHEPMAmTee0AaED0QBaAKznNGA9evr1bV8DLXdtAF9wpzRMXHxIEgpqOgY4gEkFYTEkEEkZOUVlNQRXdU99PSF3f3d1AwMbIycXEs9vX39A4NCIqJAY7DwoaQUoDPIIRTAMEYA3HABraYG44dGMhDmcAGNWeUzRLOU82X2it213AwwhXyNtcz1NTQsDR2c3a0eMc19tUyMeiMb00BnckWi6EG+BGYwU5H4lBwlAwqG4pAAZsiALYYFZDWEbLa7AoHERHHInUnnEpldwYapVGp1BrWJofEoGTRGDBGGygvTudxCMrcvQQ-pQ5hgPajLi8fgTKYzBTzJZ4qUsORy7h8SibVU7PaKLIUiRSU6FHLFdTmHzuMzmLzCoW-TTuZpuQzqDCBax6PzqaxCEVaCUDaWyqDyvUIyhIlFo1hYyi4iNa2Ex-gG+Yk-am0THC3U62IYN6BlvJmWfn2T2tIS6IzNvmaNnuPnmIXhqGrWGJJUKaZbdX4mGjRI5o2kgvZc35M6lhCBG6VcyBTzVLn-dT11x-Xn8gyC4WiwE92IEidkOMJ1HolNp3tXqCT4nGslm3LFxegYp+XQ9DqTQgyud0hDbaw91telfmsf4gSBEEwQvQYACM0J4KhaHoWBSAAKRwEYACUcBwbEvypX9VAuY8fD8NsvBCEJtD0es3h+bQ-ADYwrn9FC+nxDCsOSXCmC1MBSPIyifytP8NHdXlAm0IwwisWwbHMesTE47jrF43xDHBQTn2E7CUjwrAZVmSSyIowtKVkpQlyEeshFQwiRlhKTsUHYdDVHKFPIUby7KnPMTUOBz50tZz5JKeCKydPkgODYx-C7esVPpB1BTKL5-G0NsPKIkLRh829kXvZMcQ1TBgtC8jwo-WciwXOSaNpViMC4sEWODOwni0jlyiCQwnQadRARrAxUIq0TUms2zpOi792rizrXI5dyJQUHAIDgZQYja2KaX3WofCEYNAieF5fneFpXE03kuIDfxg1DTRUNWBIyBOkt4pCHwTDeLsu30nRdw5DwvHozogn0npvpfDJ-uo4p90bS7rtY55XgetwTGsDBIICBGQndXpIUwSNtWjXV+DRjrimPH1G20CDPC0QbhseoxrHpUmukRynkfHV8-sc9aaT8fQXRFKwt0hvd-R5J0QLbQFgSKgTqfQzCmY2lnvCuPRWKMRWIa4vdBV9QEA0FIIHQF4y9Ya8q7MNs6VLtZtaim+o6hu+tCpuIxIfXBpfiFKnJRpjMPfIr2ly0YmRQF+wwjbAN2RaeChDDiO6gmmO5s9qXTqXLlKzNoFLe3W4suBVc8uqGxAmKyJwiAA */
    id: "app",
    states: {
        LoggedOut: {
            on: {
                requestCreatePlayer: "CreatingPlayer",
                requestLogIn: "LoggingIn"
            }
        },

        LoggingIn: {
            invoke:
            {
                src: "logIn",
                input: ({ context, event }) => {
                    return { playerId: context.player?.id as UUID }
                },
                onDone: {
                    target: "Lobby",
                    actions: ["assignPlayer", "resetErrorMessages"]
                },
                onError: {
                    target: "LoggedOut",
                    actions: ["assignLogInErrors",]
                }
            }
        },
        CreatingPlayer: {
            invoke:
            {
                src: "createPlayer",
                input: ({ context, event }) => {
                    const playerName = (event as { type: "requestCreatePlayer"; playerName: string }).playerName;
                    return { playerName }
                },
                onDone: {
                    target: "LoggingIn",
                    actions: ["assignPlayer", "resetErrorMessages"]
                },
                onError: {
                    target: "LoggedOut",
                    actions: ['assignCreatePlayerErrors']
                }
            },
        },
        LoggingOut: {
            invoke:
            {
                src: "logOut",
                input: ({ context, event }) => {
                    return { playerId: context.player?.id as UUID }
                },
                onDone: {
                    target: "LoggedOut",
                    actions: ["deassignPlayer", "resetErrorMessages"]
                },
                onError: {
                    target: "Lobby",
                    actions: []
                }
            },
        },
        Lobby: {
            on: {
                requestJoinRoom: "JoiningRoom",
                requestCreateRoom: "CreatingRoom",
                requestLeaveRoom: "LoggingOut"
            }
        },

        JoiningRoom: {
            invoke: {
                src: "joinRoom",
                input: ({ context, event }) => {
                    return { roomId: 1, }
                },
                onDone: {
                    target: "Room",
                    actions: "resetErrorMessages"
                },
                onError: {
                    target: "Lobby",
                    actions: []
                }
            },
        },

        CreatingRoom: {
            invoke: {
                src: "createRoom",
                input: ({ context, event }) => {
                    const roomIn = (event as { type: "requestCreateRoom", roomIn: RoomIn }).roomIn;
                    return roomIn
                },
                onError: {
                    actions: "assignCreateRoomErrors"
                }
            },
        },

        Room: {
            on: {
                requestLeaveRoom: "Lobby",
            }
        },
    },
    initial: "LoggedOut",
    context: {
        player: null as Player | null,
        error: { type: null, messages: [] },
        gameState: null as GameState | null,
        roomState: null as RoomState | null,
        lobbyState: null as LobbyState | null
    }
})

const appActor = createActor(appMachine).start()
export default appActor