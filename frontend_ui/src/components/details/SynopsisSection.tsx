import { useState } from "react";
import { Button } from "@/components/ui/button";

export const SynopsisSection = ({ text }: { text: string }) => {
  const [expanded, setExpanded] = useState(false);
  const preview = text.slice(0, 220);

  return (
    <section className="py-8 md:py-10">
      <h2 className="mb-4 text-2xl font-medium uppercase tracking-[0.12em] text-foreground">
        Synopsis
      </h2>
      <p className="max-w-4xl text-base text-muted-foreground">
        {expanded ? text : `${preview}...`}
      </p>
      <Button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        className="mt-4 bg-card text-foreground hover:bg-muted"
      >
        {expanded ? "Read less" : "Read more"}
      </Button>
    </section>
  );
};
