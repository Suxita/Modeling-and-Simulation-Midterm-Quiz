import Link from "next/link";
import VariantList from "@/components/VariantList";

export default function VariantsPage() {
  return (
    <div className="page">
      <div className="crumbs">
        <Link href="/">← Home</Link>
      </div>
      <header className="quiz-head">
        <p className="kicker">Mode I</p>
        <h1 className="title">ვარიანტები</h1>
  
      </header>
      <VariantList />
    </div>
  );
}
