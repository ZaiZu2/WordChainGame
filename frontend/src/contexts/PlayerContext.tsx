import { createContext, useContext, useState, useEffect } from "react";
import { MePlayer, PlayerContext } from "@/types";
import { useApi } from "./ApiContext";
import { AuthError } from "../errors";
import { UUID } from "crypto";

const PlayerContextObject = createContext<PlayerContext>({
    player: null,
    logIn: () => {},
    logOut: () => {},
});

export function usePlayer() {
    return useContext(PlayerContextObject);
}

export default function PlayerProvider({ children }: { children: React.ReactNode }) {
    const api = useApi();

    const [player, setPlayer] = useState<MePlayer | null | undefined>();

    useEffect(function checkPlayerSessionCookie() {
        // If HTTP-only cookie is set and still valid, the player will get immediately
        // logged in
        (async () => {
            try {
                const response = await api.get<MePlayer>("/players/me");
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
        const response = await api.post<MePlayer>("/players/login", {}, body);
        setPlayer(response.body);
    };

    const logOut = async () => {
        await api.post<null>("/players/logout", {}, { id: player?.id });
        setPlayer(null);
    };

    return <PlayerContextObject.Provider value={{ player, logIn, logOut }}>{children}</PlayerContextObject.Provider>;
}
