import React from "react";
import { Stack } from "react-bootstrap";

import Icon from "../components/Icon";

type IconBarProps = {
    elements: {
        symbol: string;
        value: string | number;
        tooltip: string;
    }[];
};

export default function IconBar({ elements }: IconBarProps) {
    return (
        <Stack direction="horizontal" gap={2} className="justify-content-evenly">
            {elements.map((element, index) => (
                <React.Fragment key={index}>
                    {index !== 0 && <div className="vr" />}
                    <Icon {...element} />
                </React.Fragment>
            ))}
        </Stack>
    );
}
