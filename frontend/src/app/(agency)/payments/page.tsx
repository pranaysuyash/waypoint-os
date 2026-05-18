import type { Metadata } from "next";
import PageClient from "./PageClient";

export const metadata: Metadata = {
  title: "Waypoint OS — Payments",
  description: "Track payment status, due risk, and refund progress across trips.",
};

export default function Page() {
  return <PageClient />;
}

