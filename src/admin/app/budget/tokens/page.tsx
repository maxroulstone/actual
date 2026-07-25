import { BankingInstitutionCard } from "./components/BankingInstitutionCard";

export default function Tokens() {
  return (
    <div className="flex min-h-screen flex-col items-stretch justify-start gap-6 p-4">
      <div>
        <h1 className="text-4xl font-bold">Budget Tokens</h1>
        <p className="text-lg text-gray-600">
          Manage tokens for the budget here
        </p>
      </div>
      <BankingInstitutionCard name="Santander" revalidateIn="3 days" />
      <BankingInstitutionCard name="Monzo" revalidateIn="3 days" />
    </div>
  );
}
