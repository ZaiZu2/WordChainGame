import { createContext, useContext, useState } from "react";
import { MePlayer, PlayerContext } from "@/types";

const PlayerContextObject = createContext<PlayerContext>({
    player: null,
    logIn: (player: MePlayer) => {},
    logOut: () => {},
});

export function usePlayer() {
    return useContext(PlayerContextObject);
}

export default function PlayerProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    const [player, setPlayer] = useState<MePlayer | null | undefined>();

    const logIn = (player: MePlayer) => {
        setPlayer(player);
    };

    const logOut = () => {
        setPlayer(null);
    };

    return (
        <PlayerContextObject.Provider value={{ player, logIn, logOut }}>
            {children}
        </PlayerContextObject.Provider>
    );
}
