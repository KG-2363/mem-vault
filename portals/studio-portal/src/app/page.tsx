import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold tracking-tight">MemVault Studio</h1>
      <p className="text-gray-500 text-lg">Professional photo enhancement & delivery</p>
      <div className="flex gap-4">
        <Link
          href="/login"
          className="px-6 py-3 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition"
        >
          Sign In
        </Link>
        <Link
          href="/dashboard"
          className="px-6 py-3 rounded-lg border border-gray-300 font-medium hover:bg-gray-100 transition"
        >
          Dashboard
        </Link>
      </div>
    </main>
  );
}
