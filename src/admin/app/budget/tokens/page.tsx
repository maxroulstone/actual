"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, CircleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { BankingInstitution, BankingInstitutionCard } from "./components/BankingInstitutionCard";

export default function Tokens() {
  const [institutions, setInstitutions] = useState<BankingInstitution[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result] = useState<{ state: string; institution: string | null } | null>(() => {
    if (typeof window === "undefined") return null;
    const params = new URLSearchParams(window.location.search);
    const state = params.get("result");
    return state ? { state, institution: params.get("institution") } : null;
  });

  useEffect(() => {
    fetch("/api/institutions")
      .then(async (response) => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.detail || "Could not load institutions");
        return body.institutions as BankingInstitution[];
      })
      .then(setInstitutions)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Could not load institutions"));
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-stretch justify-start gap-6 p-6 md:p-10">
      <div>
        <h1 className="text-4xl font-bold">Budget Tokens</h1>
        <p className="text-lg text-gray-600">
          Review your bank connections and reauthorise them when consent expires.
        </p>
      </div>
      {result?.state === "success" && (
        <Alert>
          <CheckCircle2 />
          <AlertTitle>Bank connection updated</AlertTitle>
          <AlertDescription>{result.institution ? `${result.institution} has been reauthorised.` : "Your bank connection has been reauthorised."}</AlertDescription>
        </Alert>
      )}
      {result?.state === "error" && (
        <Alert variant="destructive">
          <CircleAlert />
          <AlertTitle>Bank reauthorisation did not complete</AlertTitle>
          <AlertDescription>Try again, or check the bank connection details.</AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <CircleAlert />
          <AlertTitle>Could not load bank connections</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {!institutions && !error && Array.from({ length: 3 }).map((_, index) => <Skeleton className="h-48 w-full" key={index} />)}
      {institutions?.map((institution) => <BankingInstitutionCard key={institution.slug} {...institution} />)}
    </div>
  );
}
