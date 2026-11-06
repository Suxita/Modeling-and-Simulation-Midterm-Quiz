import Link from "next/link";
import { allQuestions, course, variants } from "@/lib/data";

export default function Home() {
  return (
    <div className="page">
      <section className="hero">
        <p className="kicker">Midterm</p>
        <h1 className="hero-title">{course}</h1>
        <div className="rule-double" />
      </section>

      <div className="modes">
        <Link href="/variants" className="mode">
          <span className="mode-num">I</span>
          <span className="mode-name">ვარიანტები</span>
          <span className="mode-desc">
            გაიარე ტესტები ვარიანტების მიხედვით
          </span>
          <span className="mode-go">Choose a variant →</span>
        </Link>

        <Link href="/practice" className="mode">
          <span className="mode-num">II</span>
          <span className="mode-name">ყველა კითხვა</span>
          <span className="mode-desc">
            გაირე ტესტების ყველა კითხვა 
          </span>
          <span className="mode-go">Start practising →</span>
        </Link>
      </div>
    </div>
  );
}
