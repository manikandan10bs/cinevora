import { Dispatch, SetStateAction } from "react";
import { FunnelSimple } from "@phosphor-icons/react";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  genres,
  years,
  countries,
  statuses,
  contentTypes,
  sortOptions,
} from "@/data/mockContent";

export type BrowseFilters = {
  genre: string;
  year: string;
  type: string;
  country: string;
  status: string;
  sort: string;
};

type FilterPanelProps = {
  filters: BrowseFilters;
  setFilters: Dispatch<SetStateAction<BrowseFilters>>;
};

export const FilterPanel = ({ filters, setFilters }: FilterPanelProps) => {
  const fields = [
    { key: "genre", label: "Genre", values: genres },
    { key: "year", label: "Year", values: years },
    { key: "type", label: "Type", values: contentTypes },
    { key: "country", label: "Country", values: countries },
    { key: "status", label: "Status", values: statuses },
    { key: "sort", label: "Sort by", values: sortOptions },
  ] as const;

  return (
    <Card className="rounded-lg border border-border bg-card p-6">
      <div className="mb-5 flex items-center gap-3">
        <FunnelSimple size={32} weight="duotone" className="text-primary" />
        <h2 className="text-xl font-medium text-foreground">Filters</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {fields.map((field) => (
          <div key={field.key} className="space-y-2">
            <label className="text-sm text-muted-foreground">
              {field.label}
            </label>
            <Select
              value={filters[field.key]}
              onValueChange={(value) =>
                setFilters((current) => ({ ...current, [field.key]: value }))
              }
            >
              <SelectTrigger className="border-border bg-input text-foreground">
                <SelectValue placeholder={`All ${field.label}`} />
              </SelectTrigger>
              <SelectContent className="border-border bg-card text-card-foreground">
                <SelectItem value="All">All</SelectItem>
                {field.values.map((value) => (
                  <SelectItem key={value} value={value}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ))}
      </div>
    </Card>
  );
};
