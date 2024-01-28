import Modal from "react-bootstrap/Modal";
import Stack from "react-bootstrap/Stack";
import Form from "react-bootstrap/Form";
import { Button } from "react-bootstrap";
import { RefObject, useRef, useState } from "react";
import { useApi } from "../contexts/ApiContext";
import { usePlayer } from "../contexts/PlayerContext";
import { MePlayer } from "@/types";

export default function NewPlayerModal() {
    const api = useApi();
    const { player, logIn } = usePlayer();

    return (
        <Modal show={player ? false : true} centered animation>
            <Modal.Body>
                <LoginForm/>
                <SuccessfulLogin />
            </Modal.Body>
        </Modal>
    );
}

function SuccessfulLogin() {

    return (
        <></>
    )
}

function LoginForm() {
    const api = useApi();
    const { player, logIn } = usePlayer();

    const [playerErrors, setPlayerErrors] = useState<string[]>();
    const playerRef = useRef<HTMLInputElement>(null);
    const onSubmitPlayer = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const playerName = playerRef.current?.value;

        if (!playerName) {
            setPlayerErrors(["Player must not be empty"]);
            return;
        }

        const response = await api.post<MePlayer>("players", {
            name: playerName,
        });
        if (response.ok) {
            logIn(response.body);
        } else {
            console.log(response.errors);
            const errorMessages = Object.values(response.errors).reduce(
                (acc, val) => [...acc, ...val]
            );
            console.log(errorMessages);
            setPlayerErrors(errorMessages);
        }
    };

    const [codeErrors, setCodeErrors] = useState<string[]>();
    const codeRef = useRef<HTMLInputElement>(null);
    const onSubmitCode = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const code = codeRef.current?.value;

        if (!code) {
            setCodeErrors(["Code must not be empty"]);
            return;
        }

        // Query API, check the code & login
    };

    return (
        <Stack gap={4} className="justify-content">
            <Stack className="p-0">
                <div className="mx-auto mb-2 fs-3">Choose your name</div>
                <Form onSubmit={onSubmitPlayer}>
                    <InputField
                        name={"player"}
                        label={"player"}
                        type={"text"}
                        errors={playerErrors}
                        advice={"Your name must be max. 10 characters long"}
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
