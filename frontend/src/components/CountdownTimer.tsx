import React, { useEffect, useState } from "react";

type CountdownTimerProps = {
    time: number;
    start_date?: string;
    className?: string;
    precisionDigit?: number;
};

export default function CountdownTimer({
    time,
    start_date,
    className,
    precisionDigit = 1,
}: CountdownTimerProps) {
    const [countdown, setCountdown] = useState(time);

    useEffect(() => {
        const end_date = start_date
            ? new Date(new Date(start_date).getTime() + time * 1000)
            : new Date(Date.now() + time * 1000);

        setCountdown(time);

        const timerId = setInterval(() => {
            setCountdown((_) => {
                const time_left = end_date.getTime() - Date.now();
                if (time_left <= 0) {
                    clearInterval(timerId);
                    return 0;
                } else {
                    return time_left / 1000;
                }
            });
        }, 1000 / 10 ** precisionDigit);

        // Return a cleanup function that clears the interval
        return () => clearInterval(timerId);
    }, [time, start_date, precisionDigit]);
    return <div className={className}>{countdown.toFixed(precisionDigit)}</div>;
}
