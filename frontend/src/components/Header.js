import Container from 'react-bootstrap/Container';
import Navbar from 'react-bootstrap/Navbar';

export default function Header() {
    return (
        <Navbar className="bg-body-secondary">
            <Container>
                <Navbar.Brand href="#home">Word Chain Game</Navbar.Brand>
                <Navbar.Toggle />
                <Navbar.Collapse className="justify-content-end">
                    <Navbar.Text>
                        Vecky #a23df7b
                    </Navbar.Text>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
}