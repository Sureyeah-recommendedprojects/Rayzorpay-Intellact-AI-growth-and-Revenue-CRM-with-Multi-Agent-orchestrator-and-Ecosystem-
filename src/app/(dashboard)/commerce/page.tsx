import type { Metadata } from "next";

import { CommerceCrm } from "@/components/commerce/commerce-crm";

export const metadata: Metadata = { title: "Commerce CRM" };

export default function CommercePage() {
  return <CommerceCrm />;
}
