import Container from 'react-bootstrap/Container'
import Stack from 'react-bootstrap/Stack'

import Chat from './Chat'
import Lobby from './Lobby'

export default function Body() {
    return (
        <Container fluid className='p-3'>
            <Stack gap={3}>
                <Container className='border'>
                    The objective of the game is to form a chain of words where each word starts with the last letter of the
                    previous word.
                </Container>
                <Lobby />
                <Chat />
            </Stack>
        </Container>
    )
}

function Posts() {
    const authors = ['John', 'Paul', 'George', 'Ringo']
    const post = {
        id: 1,
        text: 'Hello, world!',
        timestamp: 'a minute ago',
    }

    return (
        <>
            {authors.length === 0 ?
                <p>No posts yet!</p>
                :
                <ul>
                    {authors.map(author => {
                        return (
                            <li key={post.id}>
                                <b>{author}</b> &mdash; {post.timestamp}
                                <br />
                                {post.text}
                            </li>
                        )
                    })}
                </ul>
            }
        </>
    )
}
