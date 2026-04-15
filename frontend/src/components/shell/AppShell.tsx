"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./AppShell.module.css";

interface NavItem {
  label: string;
  href: string;
}

const navItems: NavItem[] = [
  { label: "Inbox", href: "/inbox" },
  { label: "Workbench", href: "/workbench" },
  { label: "Owner Reviews", href: "/owner/reviews" },
  { label: "Owner Insights", href: "/owner/insights" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <Link href="/">Travel Agency Agent</Link>
        </div>
        <nav className={styles.nav}>
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navLink} ${
                pathname === item.href ? styles.active : ""
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}