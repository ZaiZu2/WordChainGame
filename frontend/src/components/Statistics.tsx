import { useEffect } from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import { Stack } from "react-bootstrap";
import { useStore } from "../contexts/storeContext";
import Spinner from "react-bootstrap/Spinner";
import apiClient from "../apiClient";
import { AllTimeStatistics } from "../types";

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
                <Container className="h-100 border py-2">
                    {lobbyState === null ? (
                        <Container className="d-flex">
                            <Spinner animation="border" className="my-3 mx-auto" />
                        </Container>
                    ) : (
                        Object.entries(lobbyState.stats).map(([key, value]) => {
                            return (
                                <Row>
                                    <Col>
                                        {
                                            currentStatsNameMap[
                                                key as keyof typeof currentStatsNameMap
                                            ]
                                        }
                                    </Col>
                                    <Col className="flex-shrink-1">{value}</Col>
                                </Row>
                            );
                        })
                    )}
                </Container>
                <Container className="h-100 border py-2">
                    {allTimeStatistics === undefined ? (
                        <Container className="d-flex">
                            <Spinner animation="border" className="my-2 mx-auto" />
                        </Container>
                    ) : (
                        Object.entries(allTimeStatistics).map(([key, value]) => {
                            return (
                                <Row>
                                    <Col>
                                        {
                                            allTimeStatsNameMap[
                                                key as keyof typeof allTimeStatsNameMap
                                            ]
                                        }
                                    </Col>
                                    <Col className="flex-shrink-1">{value}</Col>
                                </Row>
                            );
                        })
                    )}
                </Container>
            </Stack>
        </Container>
    );
}
