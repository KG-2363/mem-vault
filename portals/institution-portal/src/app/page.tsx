import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold tracking-tight">MemVault Institution</h1>
      <p className="text-slate-500 text-lg">School & college photo portal with face-tagging</p>
      <div className="flex gap-4">
        <Link href="/cohorts" className="px-6 py-3 rounded-lg bg-teal-600 text-white font-medium hover:bg-teal-700 transition">
          Browse Cohorts
        </Link>
        <Link href="/search" className="px-6 py-3 rounded-lg border border-slate-300 font-medium hover:bg-slate-100 transition">
          Face Search
        </Link>
      </div>
    </main>
  );
}
