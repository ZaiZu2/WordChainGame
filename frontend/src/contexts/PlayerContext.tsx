import { createContext, useContext, useState, useEffect } from "react";
import { MePlayer, PlayerContext } from "@/types";
import apiClient from "../apiClient";
import { AuthError } from "../errors";
import { UUID } from "crypto";

const PlayerContextObject = createContext<PlayerContext>({
    player: null,
    logIn: () => { },
    logOut: () => { },
});

export function usePlayer() {
    return useContext(PlayerContextObject);
}

export default function PlayerProvider({ children }: { children: React.ReactNode }) {
    const [player, setPlayer] = useState<MePlayer | null | undefined>();

    useEffect(function checkPlayerSessionCookie() {
        // If HTTP-only cookie is set and still valid, the player will get immediately
        // logged in
        (async () => {
            try {
                const response = await apiClient.get<MePlayer>("/players/me");
                setPlayer(response.body);
            } catch (error) {
                if (error instanceof AuthError) {
                    setPlayer(null);
                }
            }
        })();
    }, []);

    const logIn = async (id: UUID) => {
        const body = id === undefined ? { id: player?.id } : { id: id };
        const response = await apiClient.post<MePlayer>("/players/login", { body: body });
        setPlayer(response.body);
    };

    const logOut = async () => {
        await apiClient.post<null>("/players/logout", { body: { id: player?.id } });
        setPlayer(null);
    };

    return <PlayerContextObject.Provider value={{ player, logIn, logOut }}>{children}</PlayerContextObject.Provider>;
}
