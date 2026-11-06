import katex from "katex";

/** Renders text where segments wrapped in $...$ are LaTeX formulas. */
export default function RichText({ text }: { text: string }) {
  const parts = text.split("$");
  return (
    <>
      {parts.map((part, i) => {
        if (i % 2 === 0) return part ? <span key={i}>{part}</span> : null;
        const html = katex.renderToString(part, {
          throwOnError: false,
          output: "htmlAndMathml",
          strict: "ignore",
        });
        return <span key={i} className="math" dangerouslySetInnerHTML={{ __html: html }} />;
      })}
    </>
  );
}
