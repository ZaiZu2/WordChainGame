import Container from "react-bootstrap/Container";
import Accordion from "react-bootstrap/Accordion";
import ListGroup from "react-bootstrap/ListGroup";

export default function Rules() {
    return (
        <Container className="border">
            <Accordion defaultActiveKey="0" flush>
                <Accordion.Item eventKey="0">
                    <Accordion.Header>Rules</Accordion.Header>
                    <Accordion.Body className="p-0">
                        <ListGroup variant="flush" className="m-0">
                            <ListGroup.Item className="px-0 py-1">
                                Words must be sourced from a standard English dictionary
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                Words must consist of minimum 3 letters
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                Each word must start with the last letter of the previous word
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                No word repetitions, no proper nouns, no abbreviations, no slang
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                There's a time limit of 10 seconds per player per turn
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                Exceeding the 10 - second time limit loses you 5 points
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                Repeating a word already used in the current game loses you 5 points
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                Using an invalid word loses you 5 points
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                Being the last remaining player after all others are eliminated
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                Correct answer earns you 2 points
                            </ListGroup.Item>
                            <ListGroup.Item className="px-0 py-1">
                                You lose when your points fall below 0
                            </ListGroup.Item>
                        </ListGroup>
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
        </Container>
    );
}
