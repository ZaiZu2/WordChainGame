import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";

import { useWebSocketContext } from "../contexts/WebsocketProvider";
import { useEffect, useRef } from "react";

export default function Chat() {
    const { sendChatMessage, chatMessages } = useWebSocketContext();
    const messageInputRef = useRef<HTMLInputElement>(null);
    const lastMessageRef = useRef<HTMLDivElement>(null);

    const onSubmitMessage = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const message = messageInputRef.current?.value;
        if (message) {
            sendChatMessage(message, 1);
        }
    };

    useEffect(
        function scrollChatToBottom() {
            lastMessageRef.current?.scrollIntoView({ behavior: "auto" });
        },
        [chatMessages],
    );

    return (
        <Container className="border">
            <Container
                className="p-0 my-2"
                style={{
                    minHeight: "100px",
                    maxHeight: "300px",
                    overflowY: "auto",
                }}
            >
                {chatMessages.map((message, index) => {
                    const isLastMessage = index === chatMessages.length - 1;
                    return (
                        <div key={message.id} ref={isLastMessage ? lastMessageRef : null}>
                            {message.player_name !== "root" ? (
                                <span className="fw-bold me-2">{message.player_name}</span>
                            ) : null}
                            {message.content}
                        </div>
                    );
                })}
            </Container>
            <Form onSubmit={onSubmitMessage}>
                <Form.Control
                    type="text"
                    placeholder="Write here..."
                    className="py-1 my-2"
                    ref={messageInputRef}
                />
            </Form>
        </Container>
    );
}
