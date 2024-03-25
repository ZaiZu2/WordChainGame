import Modal from "react-bootstrap/Modal";
import Stack from "react-bootstrap/Stack";
import Form from "react-bootstrap/Form";
import { Button } from "react-bootstrap";
import { useRef, useState } from "react";
import apiClient from "../apiClient";
import { useStore } from "../contexts/storeContext";
import { RoomOut, RoomIn } from "@/types";
import { ApiError } from "../errors";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

export default function NewRoomModal() {
    const { showCreateRoomModal, toggleCreateRoomModal } = useStore();

    const [nameErrors, setErrors] = useState<string[]>([]);
    const nameRef = useRef<HTMLInputElement>(null);

    const [penalty, setPenalty] = useState(-5);
    const penaltyRef = useRef<HTMLInputElement>(null);

    const [reward, setReward] = useState(2);
    const rewardRef = useRef<HTMLInputElement>(null);

    const [startPoints, setStartPoints] = useState(0);
    const startPointsRef = useRef<HTMLInputElement>(null);

    const [roundTime, setRoundTime] = useState(10);
    const roundTimeRef = useRef<HTMLInputElement>(null);

    const [capacity, setCapacity] = useState(5);
    const capacityRef = useRef<HTMLInputElement>(null);

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const name = nameRef.current?.value;
        const capacity = capacityRef.current?.valueAsNumber;

        if (!name) {
            setErrors(["Name field must not be empty"]);
            return;
        }

        try {
            await apiClient.post<RoomOut>("/rooms", {
                body: {
                    name: name,
                    capacity: capacityRef.current?.valueAsNumber as number,
                    rules: {
                        type: "deathmatch",
                        penalty: penaltyRef.current?.valueAsNumber as number,
                        reward: rewardRef.current?.valueAsNumber as number,
                        start_score: startPointsRef.current?.valueAsNumber as number,
                        round_time: roundTimeRef.current?.valueAsNumber as number,
                    },
                } as RoomIn,
            });
        } catch (error) {
            if (error instanceof ApiError) {
                setErrors(error.messages);
            }
        }
        toggleCreateRoomModal(false);
    }

    return (
        <Modal
            centered
            animation
            show={showCreateRoomModal}
            onHide={() => toggleCreateRoomModal(false)}
        >
            <Modal.Header closeButton>
                <Modal.Title>
                    <h5 className="m-0">Create game room</h5>
                </Modal.Title>
            </Modal.Header>
            <Modal.Body className="pt-2">
                <Form onSubmit={onSubmit}>
                    <Row className="mb-2">
                        <Col>
                            <Form.Group>
                                <Form.Label>Name</Form.Label>
                                <Form.Control type="string" ref={nameRef} />
                            </Form.Group>
                        </Col>
                        <Col>
                            <Form.Group className="h-100">
                                <Form.Label>Number of players: {capacity}</Form.Label>
                                <Form.Range
                                    ref={capacityRef}
                                    defaultValue={5}
                                    max={10}
                                    min={1}
                                    onChange={(e) => setCapacity(Number(e.target.value))}
                                />
                            </Form.Group>
                        </Col>
                    </Row>
                    <Row className="mb-2">
                        <Col>
                            <Form.Group>
                                <Form.Label>Round time: {roundTime}</Form.Label>
                                <Form.Range
                                    ref={roundTimeRef}
                                    defaultValue={10}
                                    max={30}
                                    min={3}
                                    onChange={(e) => setRoundTime(Number(e.target.value))}
                                />
                            </Form.Group>
                        </Col>
                        <Col>
                            <Form.Group>
                                <Form.Label>Starting points: {startPoints}</Form.Label>
                                <Form.Range
                                    ref={startPointsRef}
                                    defaultValue={0}
                                    max={10}
                                    min={0}
                                    onChange={(e) => setStartPoints(Number(e.target.value))}
                                />
                            </Form.Group>
                        </Col>
                    </Row>
                    <Row className="mb-2">
                        <Col>
                            <Form.Group>
                                <Form.Label>Reward: {reward}</Form.Label>
                                <Form.Range
                                    ref={rewardRef}
                                    defaultValue={2}
                                    max={10}
                                    min={0}
                                    onChange={(e) => setReward(Number(e.target.value))}
                                />
                            </Form.Group>
                        </Col>
                        <Col>
                            <Form.Group>
                                <Form.Label>Penalty: {penalty}</Form.Label>
                                <Form.Range
                                    ref={penaltyRef}
                                    defaultValue={-5}
                                    max={0}
                                    min={-10}
                                    onChange={(e) => setPenalty(Number(e.target.value))}
                                />
                            </Form.Group>
                        </Col>
                    </Row>
                    <Stack direction="horizontal" gap={2}>
                        <Button variant="primary" type="submit">
                            Submit
                        </Button>
                        {nameErrors?.map((error) => {
                            return <Form.Text className="text-danger">{error}</Form.Text>;
                        })}
                    </Stack>
                </Form>
            </Modal.Body>
        </Modal>
    );
}
