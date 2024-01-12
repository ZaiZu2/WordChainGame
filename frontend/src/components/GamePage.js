import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form'

import Statistics from './Statistics'

export default function Game() {
    let gameStats = {
        currentChainLength: ['Current chain length', 6],
    }

    return (
        <>
            <Statistics stats={gameStats} />
            <ScoreCards />
            <WordList />
        </>
    );
}

function ScoreCards() {
    const player_1 = {
        id: 1,
        name: 'Vecky',
        points: 10,
        mistakes: 0,
    }
    const player_2 = {
        id: 2,
        name: 'John',
        points: 8,
        mistakes: 1,
    }
    const player_3 = {
        id: 3,
        name: 'Paul',
        points: 6,
        mistakes: 0,
    }
    const player_4 = {
        id: 4,
        name: 'George',
        points: 4,
        mistakes: 3,
    }
    const player_5 = {
        id: 5,
        name: 'Ringo',
        points: 2,
        mistakes: 2,
    }
    let players = [player_1, player_2, player_3, player_4, player_5]

    return (
        <Container className='border'>
            <Row>
                <Col className='fw-bold'>Player</Col>
                <Col className='fw-bold'>Points</Col>
                <Col className='fw-bold'>Mistakes</Col>

            </Row>
            {players.map(player => {
                return (
                    <Row key={player.id}>
                        <Col>{player.name}</Col>
                        <Col>{player.points}</Col>
                        <Col>{player.mistakes}</Col>
                    </Row>
                )
            })}
        </Container>
    )


}


function WordList() {
    const word_1 = {
        id: 1,
        userId: 1,
        sentOn: '2024-01-01 12:00:00',
        word: 'Elephant',
        isCorrect: true,
    }
    const word_2 = {
        id: 2,
        userId: 2,
        sentOn: '2024-01-01 12:01:00',
        word: 'Tiger',
        isCorrect: false,
    }
    const word_3 = {
        id: 3,
        userId: 3,
        sentOn: '2024-01-01 12:03:00',
        word: 'Rotor',
        isCorrect: false,
    }
    let words = [word_1, word_2, word_3, word_2, word_1]

    return (
        <Container className='border'>
            <Container className='text-center'>
                {words.map((word, index) => {
                    return <Word word={word} position={index} />
                })}
            </Container>
            <Form.Control type='text' placeholder='Write here...' className='py-1 my-2' />
        </Container>
    );
}

function Word({ word, position }) {
    const positionToSize = {
        0: 'fs-6',
        1: 'fs-5',
        2: 'fs-4',
        3: 'fs-3',
        4: 'fs-2',
        5: 'fs-1',
    }
    let symbol = word.isCorrect ? 'check' : 'close'
    let points = word.isCorrect ? '+2 points' : '-2 points'
    let color = word.isCorrect ? 'text-success' : 'text-danger' // GREEN or RED

    return (
        <Row>
            <Col>Vecky</Col>
            <Col className={positionToSize[position]}>{word.word}</Col>
            <Col className={`material-symbols-outlined ${color}`}>{symbol}</Col>
            <Col>{points}</Col>
        </Row>
    )
}