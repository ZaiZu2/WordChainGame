import Accordion from "react-bootstrap/Accordion";
import ListGroup from "react-bootstrap/ListGroup";

import Bubble from "./Bubble";
import Icon from "./Icon";

export default function RulesDescription() {
    const itemClassName = "px-0 py-2 d-flex align-items-center";

    return (
        <Bubble>
            <Accordion flush>
                <Accordion.Item eventKey="0">
                    <Accordion.Header>Deathmatch - rules</Accordion.Header>
                    <Accordion.Body className="p-0">
                        <ListGroup variant="flush" className="mx-2">
                            <ListGroup.Item className={itemClassName}>
                                <span>
                                    Words must be sourced from a standard English dictionary
                                </span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>
                                    Each word must start with the last letter of the previous word -
                                    either correct or wrong
                                </span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>Once used word cannot be repeated in the same game</span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>
                                    Each player has a
                                    <Icon
                                        symbol="history"
                                        iconSize={4}
                                        inline
                                        className="mx-1"
                                        style={{ verticalAlign: "bottom" }}
                                    />
                                    time limit to provide a word
                                </span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>
                                    Each players starts a game with
                                    <Icon
                                        symbol="start"
                                        iconSize={4}
                                        inline
                                        className="mx-1"
                                        style={{ verticalAlign: "bottom" }}
                                    />
                                    points
                                </span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>
                                    Repeated, invalid word or timeout results in subtraction of
                                    <Icon
                                        symbol="dangerous"
                                        iconSize={4}
                                        inline
                                        className="mx-1"
                                        style={{ verticalAlign: "bottom" }}
                                    />
                                    points
                                </span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>
                                    Correct answer earns you
                                    <Icon
                                        symbol="check"
                                        iconSize={4}
                                        inline
                                        className="mx-1"
                                        style={{ verticalAlign: "bottom" }}
                                    />
                                    points
                                </span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>You lose a game when your points fall below 0</span>
                            </ListGroup.Item>
                            <ListGroup.Item className={itemClassName}>
                                <span>The last player standing is the winner</span>
                            </ListGroup.Item>
                        </ListGroup>
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
        </Bubble>
    );
}
