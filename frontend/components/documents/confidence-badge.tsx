type ConfidenceLevel = "confident" | "partial" | "uncertain";

const LABEL: Record<ConfidenceLevel, string> = {
  confident: "Confident",
  partial: "Partial",
  uncertain: "Uncertain",
};

/** Visual marker distinguishing confident vs. partial/uncertain extraction (never presented as ground truth). */
export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  return <span className={`confidence-badge confidence-${level}`}>{LABEL[level]}</span>;
}
