import Container from 'react-bootstrap/Container';
import Navbar from 'react-bootstrap/Navbar';
import { Button } from 'react-bootstrap'

export default function Header() {
    return (
        <Navbar className="bg-body-secondary">
            <Container>
                <Navbar.Brand href="#home">Word Chain Game</Navbar.Brand>
                <Navbar.Toggle />
                <Navbar.Collapse className="justify-content-end">
                    < Button variant='primary' size='sm' className='me-3'>Create room</Button>
                    <Navbar.Text>
                        <span >Vecky</span> #a23df7b
                    </Navbar.Text>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
}