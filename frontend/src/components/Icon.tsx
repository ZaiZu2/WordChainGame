import { Stack } from "react-bootstrap";
import Tooltip from "../components/Tooltip";

type IconProps = {
    symbol: string;
    value?: string | number;
    tooltip: string;
    iconSize?: 1 | 2 | 3 | 4 | 5 | 6;
    gap?: number;
    placement?: "top" | "bottom" | "left" | "right";
    className?: string;
};

export default function Icon({
    symbol,
    value = "",
    tooltip,
    iconSize = 2,
    gap = 1,
    placement = "bottom",
    className = "",
}: IconProps) {
    return (
        <Stack direction="horizontal" gap={gap} className={className}>
            <Tooltip content={tooltip} placement={placement}>
                <span className={`material-symbols-outlined fs-${iconSize}`}>{symbol}</span>
            </Tooltip>
            <span className="fs-5">{value}</span>
        </Stack>
    );
}
