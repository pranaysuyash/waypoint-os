import Link from "next/link";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>Travel Agency Agent</h1>
        <p>AI-powered travel decision support system</p>
        <nav className={styles.nav}>
          <Link href="/inbox">Inbox</Link>
          <Link href="/workbench">Workbench</Link>
          <Link href="/owner/reviews">Owner Reviews</Link>
          <Link href="/owner/insights">Owner Insights</Link>
        </nav>
      </main>
    </div>
  );
}