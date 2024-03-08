import Modal from "react-bootstrap/Modal";
import Stack from "react-bootstrap/Stack";
import Form from "react-bootstrap/Form";
import { Button } from "react-bootstrap";
import { RefObject, useRef, useState } from "react";
import apiClient from "../apiClient";
import { usePlayer } from "../contexts/PlayerContext";
import { Room, RoomIn } from "@/types";
import { ApiError, AuthError } from "../errors";
import InputField from "./Input";

export default function NewRoomModal({
    show,
    setShow,
}: {
    show: boolean;
    setShow: (show: boolean) => void;
}) {
    const [nameErrors, setNameErrors] = useState<string[]>([]);
    const nameRef = useRef<HTMLInputElement>(null);
    const capacityRef = useRef<HTMLInputElement>(null);

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const name = nameRef.current?.value;

        if (!name) {
            setNameErrors(["Name field must not be empty"]);
            return;
        }

        try {
            await apiClient.post<Room>("/rooms", {
                body: {
                    name: name,
                    capacity: capacityRef.current?.valueAsNumber as number,
                    rules: {},
                } satisfies RoomIn,
            });
        } catch (error) {
            if (error instanceof ApiError) {
                setNameErrors(error.messages);
            }
        }
        setShow(false);
    }

    return (
        <Modal centered animation show={show} onHide={() => setShow(false)}>
            <Modal.Header closeButton>
                <Modal.Title>
                    <h5 className="m-0">Create new game room</h5>
                </Modal.Title>
            </Modal.Header>
            <Modal.Body className="pt-2">
                <Form onSubmit={onSubmit}>
                    <Form.Group className="mb-2">
                        <Form.Label>Name</Form.Label>
                        <Form.Control type="string" ref={nameRef} />
                        {nameErrors?.map((error) => {
                            return (
                                <Form.Text className="text-danger">
                                    {error}
                                </Form.Text>
                            );
                        })}
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Number of players</Form.Label>
                        <Form.Control
                            type="number"
                            defaultValue={5}
                            max={10}
                            min={1}
                            ref={capacityRef}
                        />
                    </Form.Group>

                    <Button variant="primary" type="submit">
                        Submit
                    </Button>
                </Form>
            </Modal.Body>
        </Modal>
    );
}
