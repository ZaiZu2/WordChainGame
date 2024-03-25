import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import BSTooltip from "react-bootstrap/Tooltip";
import { Placement } from "react-bootstrap/types";

export default function Tooltip({
    content,
    placement,
    children,
}: {
    content: string;
    placement: Placement;
    children: any;
}) {
    return (
        <OverlayTrigger
            key={placement}
            placement={placement}
            overlay={<BSTooltip>{content}</BSTooltip>}
        >
            {children}
        </OverlayTrigger>
    );
}
