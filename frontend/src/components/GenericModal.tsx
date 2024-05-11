import { Button, Stack } from "react-bootstrap";
import Container from "react-bootstrap/Container";
import Modal from "react-bootstrap/Modal";

import { GenericModalConfig } from "@/types";

import { useStore } from "../contexts/storeContext";

export default function GenericModal({ title, body }: GenericModalConfig) {
    const { toggleModal, modalConfigs } = useStore();

    return (
        <Modal
            centered
            animation
            show={Boolean(modalConfigs.generic)}
            onHide={() => toggleModal("generic", undefined, true)}
        >
            {title && (
                <Modal.Header>
                    <Modal.Title className="text-center">
                        <h5 className="m-0">{title}</h5>
                    </Modal.Title>
                </Modal.Header>
            )}
            {
                <Modal.Body className="pt-2">
                    <Stack gap={2} className="d-flex">
                        {body && <Container>{body}</Container>}
                        <Button
                            variant="primary"
                            onClick={() => toggleModal("generic", undefined, true)}
                            className="mx-auto"
                        >
                            Close
                        </Button>
                    </Stack>
                </Modal.Body>
            }
        </Modal>
    );
}
