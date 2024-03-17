import Container from 'react-bootstrap/Container'
import Form from 'react-bootstrap/Form'
import Table from 'react-bootstrap/Table'

import Statistics from '../components/Statistics'
import { Word } from '../types'

export default function RoomPage() {
    let gameStats: Record<string, [string, string | number]> = {
        currentChainLength: ['Current chain length', 6],
    }

    return (
        <>
            <Statistics stats={gameStats} />
            <ScoreCard />
            <WordList />
        </>
    );
}

function ScoreCard() {
    const player_1 = {
        id: 1,
        name: 'Vecky',
        points: 10,
        mistakes: 0,
        ranking: 0,
    }
    const player_2 = {
        id: 2,
        name: 'John',
        points: 8,
        mistakes: 1,
        ranking: 1,
    }
    const player_3 = {
        id: 3,
        name: 'Paul',
        points: 6,
        mistakes: 0,
        ranking: 2,
    }
    const player_4 = {
        id: 4,
        name: 'George',
        points: 4,
        mistakes: 3,
        ranking: 3,
    }
    const player_5 = {
        id: 5,
        name: 'Ringo',
        points: 2,
        mistakes: 2,
        ranking: 4,
    }
    let players = [player_1, player_2, player_3, player_4, player_5]

    const style = {
        flexBasis: "25%"
    }

    return (
        <Container className='border'>
            <Table borderless className='m-0 text-center'>
                <thead>
                    <tr className="d-flex py-2 justify-content-between">
                        <td style={style} className='p-0 border-0 text-start fw-bold'>#</td>
                        <td style={style} className='p-0 border-0 text-end fw-bold'>Player</td>
                        <td style={style} className='p-0 border-0 text-end fw-bold'>Points</td>
                        <td style={style} className='p-0 border-0 text-end fw-bold'>Mistakes</td>
                    </tr>
                </thead>
                <tbody className='border-top'>
                    {players.map(player => {
                        return (
                            <tr key={player.id} className="d-flex py-1 justify-content-between">
                                <td style={style} className='p-0 border-0 text-start'>{player.ranking + 1}</td>
                                <td style={style} className='p-0 border-0 text-end'>{player.name}</td>
                                <td style={style} className='p-0 border-0 text-end'>{player.points}</td>
                                <td style={style} className='p-0 border-0 text-end'>{player.mistakes}</td>
                            </tr>
                        )
                    })}
                </tbody>
            </Table>
        </Container>
    )
}


function WordList() {
    const positionToSize: Record<number, string> = {
        0: 'fs-6',
        1: 'fs-5',
        2: 'fs-4',
        3: 'fs-3',
        4: 'fs-2',
        5: 'fs-1',
    }
    let symbol = (word: Word) => word.is_correct ? 'check' : 'close'
    let points = (word: Word) => word.is_correct ? '+2' : '-2'
    let color = (word: Word) => word.is_correct ? 'text-success' : 'text-danger' // GREEN or RED

    const word_1 = {
        id: 1,
        player_name: 'Vecky',
        created_on: new Date('2024-01-01 12:00:00'),
        content: 'Elephant',
        is_correct: true,
        game_id: 1,
    } as Word;
    const word_2 = {
        id: 2,
        player_name: 'Adam',
        created_on: new Date('2024-01-01 12:00:00'),
        content: 'Tiger',
        is_correct: false,
        game_id: 1,
    } as Word;
    const word_3 = {
        id: 3,
        player_name: "Becky",
        created_on: new Date('2024-01-01 12:00:00'),
        content: 'Rotor',
        is_correct: false,
        game_id: 1,
    } as Word;
    let words = [word_1, word_2, word_3, word_2, word_1]

    const style = {
        flexGrow: 1,
        flexShrink: 0,
        justifyContent: 'center',
        alignItems: 'center'
    };

    return (
        <Container className='border'>
            <Table borderless className='m-0 text-center'>
                <tbody>
                    {words.map((word, position) => {
                        return <tr style={style} className="d-flex justify-content-between">
                            <td style={{ flexBasis: "20%" }} className='p-0 border-0'>{word.player_name}</td>
                            <td style={{ flexBasis: "60%" }} className={`p-0 border-0 ${positionToSize[position]}`}>{word.content}</td>
                            <td style={{ flexBasis: "10%" }} className={`p-0 border-0 material-symbols-outlined ${color(word)}`}>{symbol(word)}</td>
                            <td style={{ flexBasis: "10%" }} className={'p-0 border-0'}>{points(word)}</td>
                        </tr>
                    })}
                    <tr style={style} className="d-flex justify-content-between">
                        <td style={{ flexBasis: "20%" }} className='p-0 border-0'>Vecky</td>
                        <td style={{ flexBasis: "60%" }} className={`p-0 border-0 ${positionToSize[5]}`}>...</td>
                        <td style={{ flexBasis: "10%" }} className={'p-0 border-0'}>...</td>
                        <td style={{ flexBasis: "10%" }} className={'p-0 border-0'}>...</td>
                    </tr>
                </tbody>
            </Table>
            <Form.Control type='text' placeholder='Write here...' className='py-1 mt-0 mb-2' />
        </Container>
    );
}