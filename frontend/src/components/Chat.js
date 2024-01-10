import Container from 'react-bootstrap/Container'
import Form from 'react-bootstrap/Form'

export default function Chat() {
    const message_1 = {
        id: 1,
        name: 'Vecky',
        sentOn: '2024-01-01 12:00:00',
        message: 'I love playing this game!'
    }
    const message_2 = {
        id: 2,
        name: 'Jordan',
        sentOn: '2024-01-01 12:01:00',
        message: 'This is my favorite game!'
    }
    const message_3 = {
        id: 3,
        name: 'Bobba',
        sentOn: '2024-01-01 12:03:00',
        message: 'Wohoho, what a game!'
    }
    let messages = [message_1, message_2, message_3]

    return (
        <Container className='border'>
            {messages.map(message => {
                return (
                    <div key={message.id}>
                        <span className='fst-italic'>{message.sentOn} </span>
                        <span className='fw-bold'>{message.name} </span>
                        {message.message}
                    </div>
                )
            })
            }
            <Form.Control type='text' placeholder='Write here...' className='py-1 my-2' />
        </Container>
    )
}