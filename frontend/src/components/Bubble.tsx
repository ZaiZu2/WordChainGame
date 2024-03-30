import Container from "react-bootstrap/Container";

export default function Bubble({ children }: { children: React.ReactNode }) {
    return <Container className="p-2 border rounded-3">{children}</Container>;
}
