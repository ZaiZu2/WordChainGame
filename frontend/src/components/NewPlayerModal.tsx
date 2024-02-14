import Modal from "react-bootstrap/Modal";
import Stack from "react-bootstrap/Stack";
import Form from "react-bootstrap/Form";
import { Button } from "react-bootstrap";
import { RefObject, useRef, useState } from "react";
import apiClient from "../apiClient";
import { usePlayer } from "../contexts/PlayerContext";
import { MePlayer } from "@/types";
import { ApiError, AuthError } from "../errors";
import { UUID } from "crypto";

export function LoginModal() {
    const { logIn } = usePlayer();

    const [playerErrors, setPlayerErrors] = useState<string[]>();
    const playerRef = useRef<HTMLInputElement>(null);
    const onSubmitPlayer = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const playerName = playerRef.current?.value;

        if (!playerName) {
            setPlayerErrors(["Player field must not be empty"]);
            return;
        }

        try {
            const response = await apiClient.post<MePlayer>(
                "/players",
                { body: { name: playerName }, }
            );
            await logIn(response.body.id);
        } catch (error) {
            if (error instanceof ApiError || error instanceof AuthError) {
                const errorMessages = Object.values(error.errorMessages).reduce(
                    (acc, val) => [...acc, ...val]
                );
                setPlayerErrors(errorMessages);
            }
        }
    };

    const [codeErrors, setCodeErrors] = useState<string[]>();
    const codeRef = useRef<HTMLInputElement>(null);
    const onSubmitCode = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const code = codeRef.current?.value;

        if (!code) {
            setCodeErrors(["Code field must not be empty"]);
            return;
        }

        try {
            await logIn(code as UUID);
        } catch (error) {
            if (error instanceof ApiError) {
                const errorMessages = Object.values(error.errorMessages).reduce(
                    (acc, val) => [...acc, ...val]
                );
                setCodeErrors(errorMessages);
            }
        }
    };

    return (
        <Modal centered animation show>
            <Modal.Body>
                <Stack gap={4} className="justify-content">
                    <Stack className="p-0">
                        <div className="mx-auto mb-2 fs-3">
                            Choose your name
                        </div>
                        <Form onSubmit={onSubmitPlayer}>
                            <InputField
                                name={"player"}
                                label={"player"}
                                type={"text"}
                                errors={playerErrors}
                                advice={
                                    "Your name must be max. 10 characters long"
                                }
                                fieldRef={playerRef}
                            />
                        </Form>
                    </Stack>
                    <Stack className="p-0">
                        <div className="mx-auto mb-2 fs-3">
                            Or provide your unique code
                        </div>
                        <Form onSubmit={onSubmitCode}>
                            <InputField
                                name={"player"}
                                label={"player"}
                                type={"text"}
                                errors={codeErrors}
                                advice={
                                    "It was provided to you when you first created your account"
                                }
                                fieldRef={codeRef}
                            />
                        </Form>
                    </Stack>
                </Stack>
            </Modal.Body>
        </Modal>
    );
}

const InputField: React.FC<{
    name: string;
    label: string;
    type?: string;
    placeholder?: string;
    errors?: string[];
    advice?: string;
    fieldRef: RefObject<HTMLInputElement>;
}> = (props) => {
    return (
        <Form.Group
            controlId={props.name}
            className="d-flex flex-column justify-content"
        >
            <Form.Label hidden>{props.label}</Form.Label>
            <Stack className="mx-auto m-1" direction="horizontal" gap={3}>
                <Form.Control
                    type={props.type || "text"}
                    ref={props.fieldRef}
                    placeholder={props.placeholder}
                    className="w-75 m-0 mx-auto"
                />
                <Button type="submit" className="m-0 mx-auto">
                    Submit
                </Button>
            </Stack>
            {props.errors?.length ? (
                props.errors.map((error) => {
                    return (
                        <Form.Text className="text-danger mx-auto">
                            {error}
                        </Form.Text>
                    );
                })
            ) : (
                <Form.Text muted className="mx-auto">
                    {props.advice}
                </Form.Text>
            )}
        </Form.Group>
    );
};
