"use client"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiRequest } from "@/lib/api"
import { Button } from "./ui/button"

export default function Header() {
    const router = useRouter();

    const handleLogout = async () => {
        try {
            await apiRequest("/api/auth/logout", { method: "POST" });
            router.push("/login"); // Redirect to login
        } catch (err) {
            console.error("Logout failed", err);
        }
    };

    return (
    <header className="flex items-center justify-between p-4 border-b bg-white">
      <Link href="/" className="text-xl font-bold">
        ShareNotes
      </Link>
      <div className="flex items-center space-x-4">
        <Link href="/" className="hover:underline">
          Home
        </Link>
        <Link href="/settings" className="hover:underline">
          Settings
        </Link>
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </div>
    </header>
  );
};

