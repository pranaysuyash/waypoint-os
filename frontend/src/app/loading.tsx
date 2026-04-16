import { Spinner } from "@/components/ui/loading";

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080a0c]">
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p className="text-[12px] text-[#8b949e]">Loading...</p>
      </div>
    </div>
  );
}
