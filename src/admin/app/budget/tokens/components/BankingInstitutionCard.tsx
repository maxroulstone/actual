"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RefreshCw } from "lucide-react";
import { useState } from "react";

export type BankingInstitution = {
  slug: string;
  name: string;
  status: "healthy" | "needs_attention" | "not_connected";
  last_token_update_at: number | null;
  last_successful_import_at: number | null;
  last_failure_at: number | null;
  last_failure_message: string | null;
};

type BankingInstitutionCardProps = BankingInstitution;

const statusCopy = {
  healthy: { label: "Healthy", variant: "secondary" as const },
  needs_attention: { label: "Needs attention", variant: "destructive" as const },
  not_connected: { label: "Not connected", variant: "outline" as const },
};

function formatDate(timestamp: number | null) {
  if (!timestamp) return "Never";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp * 1000));
}

export function BankingInstitutionCard({
  slug,
  name,
  status,
  last_token_update_at,
  last_successful_import_at,
  last_failure_message,
}: BankingInstitutionCardProps) {
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const statusInfo = statusCopy[status];

  async function revalidate() {
    setIsStarting(true);
    setError(null);
    try {
      const response = await fetch(`/api/institutions/${slug}/reauthorize`, {
        method: "POST",
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Could not start reauthorisation");
      window.location.assign(body.authorization_url);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not start reauthorisation");
      setIsStarting(false);
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{name}</CardTitle>
        <CardDescription>TrueLayer connection</CardDescription>
        <CardAction>
          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm text-muted-foreground">
        <p>Token last updated: {formatDate(last_token_update_at)}</p>
        <p>Last successful import: {formatDate(last_successful_import_at)}</p>
        {last_failure_message && <p className="text-destructive">Latest issue: {last_failure_message}</p>}
      </CardContent>
      <div className="flex items-center justify-between gap-3 px-6">
        <p className="text-xs text-muted-foreground">This opens your bank’s secure authorisation flow.</p>
        <Button onClick={revalidate} disabled={isStarting}>
          <RefreshCw className={isStarting ? "animate-spin" : ""} />
          {isStarting ? "Opening bank…" : "Revalidate"}
        </Button>
      </div>
      {error && <p className="px-6 text-sm text-destructive">{error}</p>}
    </Card>
  );
}
