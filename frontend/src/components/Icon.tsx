import { Stack } from "react-bootstrap";

import Tooltip from "../components/Tooltip";

type IconProps = {
    symbol: string;
    value?: string | number;
    tooltip?: string;
    color?: string;
    iconSize?: 1 | 2 | 3 | 4 | 5 | 6;
    textSize?: 1 | 2 | 3 | 4 | 5 | 6;
    gap?: number;
    inline?: boolean;
    placement?: "top" | "bottom" | "left" | "right";
    className?: string;
    style?: React.CSSProperties;
};

export default function Icon({
    symbol,
    value,
    tooltip,
    color,
    iconSize = 2,
    textSize = 5,
    gap = 3,
    inline = false,
    placement = "bottom",
    className = "",
    style = {},
}: IconProps) {
    return (
        <Stack
            direction="horizontal"
            gap={gap}
            className={`${inline ? "d-inline-flex" : ""} ${className}`}
            style={style}
        >
            {tooltip !== undefined ? (
                <Tooltip content={tooltip} placement={placement}>
                    <span className={`material-symbols-outlined fs-${iconSize} ${color}`}>
                        {symbol}
                    </span>
                </Tooltip>
            ) : (
                <span className={`material-symbols-outlined fs-${iconSize}`}>{symbol}</span>
            )}
            {value && <span className={`fs-${textSize}`}>{value}</span>}
        </Stack>
    );
}
