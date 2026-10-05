import type { Installment, MarketCode } from "../api";
import { formatDueDate, formatMoney } from "../format";

interface ScheduleTableProps {
    market: MarketCode;
    installments: Installment[];
    caption: string;
}

export function ScheduleTable({ market, installments, caption }: ScheduleTableProps) {
    return (
        <table className="schedule">
            <caption>{caption}</caption>
            <thead>
                <tr>
                    <th scope="col">#</th>
                    <th scope="col">Due</th>
                    <th scope="col">Amount</th>
                </tr>
            </thead>
            <tbody>
                {installments.map((item) => (
                    <tr key={item.sequence}>
                        <td>{item.sequence}</td>
                        <td>{formatDueDate(item.due_date, market)}</td>
                        <td>{formatMoney(item.amount, market)}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
