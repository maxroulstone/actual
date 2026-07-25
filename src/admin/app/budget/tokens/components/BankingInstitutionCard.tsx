import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type BankingInstitutionCardProps = {
  name: string;
  revalidateIn: string;
};

export function BankingInstitutionCard({
  name,
  revalidateIn,
}: BankingInstitutionCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{name}</CardTitle>
        <CardDescription>Revalidate in {revalidateIn}</CardDescription>
        <CardAction>
          <Button variant="secondary">Revalidate</Button>
        </CardAction>
      </CardHeader>
    </Card>
  );
}
