export type DemoCredential = {
  role: "admin" | "officer" | "bidder";
  label: string;
  email: string;
  password: string;
  description: string;
};

/**
 * Accounts created by scripts/seed.py and backend/app/autoseed.py.
 * Offered on the login form so reviewers can sign in without a walkthrough.
 */
export const DEMO_CREDENTIALS: DemoCredential[] = [
  {
    role: "admin",
    label: "Admin",
    email: "admin@demo.gov.in",
    password: "admin1234",
    description: "Manage users & settings",
  },
  {
    role: "officer",
    label: "Procurement Officer",
    email: "officer@demo.gov.in",
    password: "demo1234",
    description: "Verify bids & compliance",
  },
  {
    role: "bidder",
    label: "Bidder / Supplier",
    email: "bidder@demo.com",
    password: "demo1234",
    description: "Submit & track bids",
  },
];
