import { Spinner } from "@/components/ui/loading";

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080a0c]">
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p className="text-[12px] text-[#6e7681]">Loading...</p>
      </div>
    </div>
  );
}
