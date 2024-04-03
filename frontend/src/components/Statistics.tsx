import { useEffect } from "react";
import { Stack } from "react-bootstrap";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Spinner from "react-bootstrap/Spinner";

import apiClient from "../apiClient";
import { useStore } from "../contexts/storeContext";
import { AllTimeStatistics } from "../types";
import Bubble from "./Bubble";

export default function Statistics() {
    const { lobbyState, allTimeStatistics, setAllTimeStatistics } = useStore();

    const currentStatsNameMap = {
        active_players: "Active players",
        active_rooms: "Active rooms",
    };
    const allTimeStatsNameMap = {
        longest_chain: "Longest chain built",
        longest_game_time: "Longest game played",
        total_games: "Total games played",
    };

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
        <Container className="px-0">
            <Stack gap={3} direction="horizontal">
                <Bubble>
                    {lobbyState === null ? (
                        <Container className="d-flex">
                            <Spinner animation="border" className="my-3 mx-auto" />
                        </Container>
                    ) : (
                        Object.entries(lobbyState.stats).map(([key, value]) => {
                            return (
                                <Row key={key}>
                                    <Col>
                                        {
                                            currentStatsNameMap[
                                                key as keyof typeof currentStatsNameMap
                                            ]
                                        }
                                    </Col>
                                    <Col>{value}</Col>
                                </Row>
                            );
                        })
                    )}
                </Bubble>
                <Bubble>
                    {allTimeStatistics === undefined ? (
                        <Container className="d-flex">
                            <Spinner animation="border" className="my-2 mx-auto" />
                        </Container>
                    ) : (
                        Object.entries(allTimeStatistics).map(([key, value]) => {
                            return (
                                <Row key={key}>
                                    <Col>
                                        {
                                            allTimeStatsNameMap[
                                                key as keyof typeof allTimeStatsNameMap
                                            ]
                                        }
                                    </Col>
                                    <Col>{value}</Col>
                                </Row>
                            );
                        })
                    )}
                </Bubble>
            </Stack>
        </Container>
    );
}
