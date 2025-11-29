import express, { Request, Response } from "express";
import * as actual from "@actual-app/api";
import dotenv from "dotenv";

dotenv.config(); // Load .env file if present

// --- ENV VARIABLES ---
const SERVER_URL = process.env.ACTUAL_URL!;
const BUDGET_ID = process.env.BUDGET_ID!;
const FILE_PASSWORD = process.env.FILE_PASSWORD || undefined;

// --- TYPES ---
interface TrueLayerMeta {
  provider_merchant_name?: string;
  address?: string;
}

interface TrueLayerTransaction {
  timestamp: string;
  description: string;
  transaction_type: "DEBIT" | "CREDIT";
  amount: number;
  transaction_id: string;
  meta?: TrueLayerMeta;
}

interface ActualTransaction {
  account: string;
  date: string;
  payee_name: string;
  amount: number; // integer cents
  imported_id: string;
  notes?: string;
}

// --- CONVERTER ---
function convertTrueLayerToActual(
  t: TrueLayerTransaction,
  accountId: string
): ActualTransaction {
  let amount = t.amount;

  if (t.transaction_type === "DEBIT" && amount > 0) {
    amount = -amount;
  } else if (t.transaction_type === "CREDIT" && amount < 0) {
    amount = -amount;
  }

  const payee = t.meta?.provider_merchant_name || t.description;

  const notes = [t.description, t.meta?.address].filter(Boolean).join(" | ");

  return {
    account: accountId,
    date: t.timestamp.slice(0, 10),
    payee_name: payee,
    amount: Math.round(amount * 100),
    imported_id: t.transaction_id,
    notes,
  };
}

// --- EXPRESS APP ---
const app = express();
app.use(express.json());

app.get("/health", (req: Request, res: Response) => {
  res.json({ status: "ok" });
});

// Quick config introspection (no secrets)
app.get("/config", (req: Request, res: Response) => {
  res.json({
    serverURL: SERVER_URL,
    budgetId: BUDGET_ID,
    hasPassword: Boolean(FILE_PASSWORD),
  });
});

app.get("/accounts", async (req: Request, res: Response) => {
  try {
    await actual.init({
      dataDir: "./data",
      serverURL: SERVER_URL,
      password: FILE_PASSWORD,
    });

    await actual.downloadBudget(BUDGET_ID);

    const accounts = await actual.getAccounts();

    await actual.shutdown();

    res.json({ status: "ok", accounts });
  } catch (err: any) {
    console.error(err);
    res.status(500).json({ error: err.message || String(err) });
  } finally {
    // ensure Actual is shutdown
    try {
      await actual.shutdown();
    } catch {}
  }
});

// POST /import  -  receive TrueLayer tx -> write to Actual
app.post("/import", async (req: Request, res: Response) => {
  try {
    const transactions: TrueLayerTransaction[] = req.body.transactions;

    await actual.init({
      dataDir: "./data",
      serverURL: SERVER_URL,
      password: FILE_PASSWORD,
    });

    await actual.downloadBudget(BUDGET_ID);

    const converted = transactions.map((t) =>
      convertTrueLayerToActual(t, req.body.account_id)
    );
    const result = await actual.importTransactions(
      req.body.account_id,
      converted
    );

    await actual.shutdown();

    res.json({
      status: "ok",
      imported: converted.length,
      result,
    });
  } catch (err: any) {
    console.error(err);
    res.status(500).json({ error: err.message || String(err) });
  } finally {
    // ensure Actual is shutdown
    try {
      await actual.shutdown();
    } catch {}
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Actual writer running on port ${PORT}`);
});
