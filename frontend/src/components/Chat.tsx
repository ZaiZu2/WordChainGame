import Container from "react-bootstrap/Container"
import Form from "react-bootstrap/Form"

import { useWebSocketContext } from "../contexts/WebsocketProvider"
import { useRef } from "react"

export default function Chat() {
    const { sendChatMessage, chatMessages, } = useWebSocketContext();
    const messageInputRef = useRef<HTMLInputElement>(null);

    const onSubmitMessage = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const message = messageInputRef.current?.value;
        if (message) {
            sendChatMessage(message, 1);
        }
    };

    return (
        <Container className="border p-2">
            <Container className="px-1 pb-2">
                {chatMessages.map((message) => {
                    return (
                        <div key={message.id}>
                            {message.player_name !== "root"
                                ? <span className="fw-bold me-2">{message.player_name}</span>
                                : null}
                            {message.content}
                        </div>
                    );
                })}
            </Container>
            <Form onSubmit={onSubmitMessage}>
                <Form.Control
                    type="text"
                    placeholder="Write here..."
                    className="py-1 m-0"
                    ref={messageInputRef}
                />
            </Form>
        </Container>
    );
}
