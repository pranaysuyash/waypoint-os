import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Waypoint OS",
  description:
    "The operating system for boutique travel agencies — from messy intake to client-safe proposals.",
};

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
