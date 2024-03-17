
import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'

export default function Statistics({ stats }: { stats: Record<string, [string, string | number]>}) {
    return (
        <Container className='border'>
            <Row>
                {Object.entries(stats).map(([key, values]) => {
                    return (
                        <Col key={key}>{values[0]}: {values[1]}</Col>
                    )
                })}
            </Row>
        </Container >
    )
}