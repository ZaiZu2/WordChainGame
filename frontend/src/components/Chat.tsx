import { useEffect, useRef } from "react";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";

import { useStore } from "../contexts/storeContext";
import { useWebSocketContext } from "../contexts/WebsocketProvider";
import Bubble from "./Bubble";

export default function Chat() {
    const { chatMessages } = useStore();
    const { sendChatMessage } = useWebSocketContext();
    const messageInputRef = useRef<HTMLInputElement>(null);
    const lastMessageRef = useRef<HTMLDivElement>(null);

    const onSubmitMessage = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const message = messageInputRef.current?.value;
        if (message) {
            sendChatMessage(message);
            messageInputRef.current!.value = "";
        }
    };

    useEffect(
        function scrollChatToBottom() {
            lastMessageRef.current?.scrollIntoView({ behavior: "auto" });
        },
        [chatMessages]
    );

    return (
        <Bubble>
            <Container
                fluid
                className="p-0 px-1"
                style={{
                    minHeight: "100px",
                    maxHeight: "300px",
                    overflowY: "auto",
                    wordBreak: "break-word", // Add this line to break long words
                }}
            >
                {chatMessages.map((message, index) => {
                    const isLastMessage = index === chatMessages.length - 1;
                    return (
                        <div key={message.id} ref={isLastMessage ? lastMessageRef : null}>
                            {message.player_name !== "root" ? (
                                <>
                                    <span className="fw-bold me-2">{message.player_name}</span>
                                    {message.content}
                                </>
                            ) : (
                                <span className="fst-italic">{message.content}</span>
                            )}
                        </div>
                    );
                })}
            </Container>
            <Form onSubmit={onSubmitMessage}>
                <Form.Control
                    type="text"
                    placeholder="Write here..."
                    className="py-1 mt-2"
                    ref={messageInputRef}
                />
            </Form>
        </Bubble>
    );
}
