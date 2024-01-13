import Container from 'react-bootstrap/Container';
import Navbar from 'react-bootstrap/Navbar';
import { Button } from 'react-bootstrap'
import { Link } from 'react-router-dom'

import GamePage from '../pages/GamePage';

export default function Header() {
    return (
        <Navbar className="bg-body-secondary">
            <Container>
                <Navbar.Brand href="#home">Word Chain Game</Navbar.Brand>
                <Navbar.Toggle />
                <Navbar.Collapse className="justify-content-end">
                    < Button as={Link} to='/' end variant='primary' size='sm' className='me-3'>Lobby</Button>
                    < Button as={Link} to='/game/1' elements={<GamePage />} variant='primary' size='sm' className='me-3'>Game</Button>

                    < Button variant='primary' size='sm' className='me-3'>Create room</Button>
                    <Navbar.Text>
                        <span >Vecky</span> #a23df7b
                    </Navbar.Text>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
}