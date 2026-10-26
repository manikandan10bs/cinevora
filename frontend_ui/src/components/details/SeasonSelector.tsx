import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Season } from "@/data/mockContent";

type SeasonSelectorProps = {
  seasons: Season[];
  selectedSeasonId: string;
  onSelect: (value: string) => void;
};

export const SeasonSelector = ({
  seasons,
  selectedSeasonId,
  onSelect,
}: SeasonSelectorProps) => {
  return (
    <div className="max-w-xs">
      <label className="mb-2 block text-sm text-muted-foreground">Season</label>
      <Select value={selectedSeasonId} onValueChange={onSelect}>
        <SelectTrigger className="border-border bg-input text-foreground">
          <SelectValue placeholder="Select season" />
        </SelectTrigger>
        <SelectContent className="border-border bg-card text-card-foreground">
          {seasons.map((season) => (
            <SelectItem key={season.id} value={season.id}>
              {season.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
