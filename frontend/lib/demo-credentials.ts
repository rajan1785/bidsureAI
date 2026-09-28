export type DemoCredential = {
  role: "admin" | "officer" | "bidder";
  label: string;
  email: string;
  password: string;
  description: string;
};

/**
 * Accounts created by scripts/seed.py and backend/app/autoseed.py.
 * Shown on the homepage so reviewers can sign in without a walkthrough.
 */
export const DEMO_CREDENTIALS: DemoCredential[] = [
  {
    role: "officer",
    label: "Procurement Officer",
    email: "officer@demo.gov.in",
    password: "demo1234",
    description: "Review tenders, bids and compliance results",
  },
  {
    role: "bidder",
    label: "Bidder / Supplier",
    email: "bidder@demo.com",
    password: "demo1234",
    description: "Submit documents and track verification",
  },
  {
    role: "admin",
    label: "Administrator",
    email: "admin@demo.gov.in",
    password: "admin1234",
    description: "Approve pending registrations and manage users",
  },
];
