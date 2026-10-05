import type { MarketCode, Offer } from "../api";
import { formatApr, formatMoney } from "../format";

interface OfferListProps {
    market: MarketCode;
    offers: Offer[];
    selectedTerm: number | null;
    onSelect: (term: number) => void;
}

export function OfferList({ market, offers, selectedTerm, onSelect }: OfferListProps) {
    return (
        <fieldset className="offers">
            <legend>Choose how to pay</legend>
            {offers.map((offer) => (
                <label key={offer.term} className={offer.term === selectedTerm ? "offer offer--selected" : "offer"}>
                    <input
                        type="radio"
                        name="term"
                        value={offer.term}
                        checked={offer.term === selectedTerm}
                        onChange={() => onSelect(offer.term)}
                    />
                    <span className="offer__payment">
                        {formatMoney(offer.monthly_payment, market)}
                        <small>/month</small>
                    </span>
                    <span className="offer__term">{offer.term} months</span>
                    <span className="offer__apr">{formatApr(offer.apr)}</span>
                    <span className="offer__total">Total {formatMoney(offer.total_payable, market)}</span>
                </label>
            ))}
        </fieldset>
    );
}
