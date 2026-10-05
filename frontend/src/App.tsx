import { useMemo } from "react";

import { createApi } from "./api";
import { Checkout } from "./components/Checkout";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function App() {
    const api = useMemo(() => createApi(API_URL), []);
    return (
        <main>
            <header>
                <h1>Checkout</h1>
                <p>Split your purchase into monthly payments. No late fees, no surprises.</p>
            </header>
            <Checkout api={api} initialAmount="1240.00" />
        </main>
    );
}
