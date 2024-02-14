import Stack from "react-bootstrap/Stack"
import Form from "react-bootstrap/Form"
import { Button } from "react-bootstrap"
import { RefObject } from "react"

const InputField: React.FC<{
    name: string;
    label: string;
    type?: string;
    placeholder?: string;
    errors?: string[];
    advice?: string;
    fieldRef: RefObject<HTMLInputElement>;
}> = (props) => {
    return (
        <Form.Group
            controlId={props.name}
            className="d-flex flex-column justify-content"
        >
            <Form.Label hidden>{props.label}</Form.Label>
            <Stack className="mx-auto m-1" direction="horizontal" gap={3}>
                <Form.Control
                    type={props.type || "text"}
                    ref={props.fieldRef}
                    placeholder={props.placeholder}
                    className="w-75 m-0 mx-auto"
                />
                <Button type="submit" className="m-0 mx-auto">
                    Submit
                </Button>
            </Stack>
            {props.errors?.length ? (
                props.errors.map((error) => {
                    return (
                        <Form.Text className="text-danger mx-auto">
                            {error}
                        </Form.Text>
                    );
                })
            ) : (
                <Form.Text muted className="mx-auto">
                    {props.advice}
                </Form.Text>
            )}
        </Form.Group>
    );
};
export default InputField;