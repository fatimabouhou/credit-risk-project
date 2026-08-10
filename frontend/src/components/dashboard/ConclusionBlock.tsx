import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";

interface ConclusionBlockProps {
  conclusion: string;
}

export default function ConclusionBlock({ conclusion }: ConclusionBlockProps) {
  const paragraphs = conclusion.split("\n\n");

  return (
    <Card>
      <SectionHeader title="Conclusion de l'agent d'analyse" />
      <div className="max-w-3xl space-y-5">
        {paragraphs.map((p, i) => (
          <p key={i} className="text-base leading-relaxed text-text-primary">
            {p}
          </p>
        ))}
      </div>
    </Card>
  );
}
