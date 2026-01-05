"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import FileList from "@/components/FileList";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function Home() {

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [status, setStatus] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    apiRequest("/api/status")
    .then((data) => {
      if (!data.online) router.push("/login"); // Redirect if offline
      setStatus(data);
    })
    .catch(() => router.push("/login"));
  }, [router]);

  const handleSearch = async () => {
    if (!query) return;
    try {
      const data = await apiRequest(`/api/search?q=${query}`);
      console.log(data)
      setResults(data || []);
    } catch (err) {
      console.log(err)
      setResults([]);
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };
  // Prevent rendering if not authenticated (optional, avoids flash of content)
  if (!status) return null;

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-50">
      
      {/* Container for main content */}
      <div className="w-full max-w-4xl space-y-8">
        
        {/* Header Section */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900">
            File Search
          </h1>
          <p className="text-gray-500">
            Find and download the file you want securely.
          </p>
        </div>

        {/* Search Bar Section */}
        <div className="flex w-full items-center space-x-2 bg-white p-4 rounded-lg shadow-sm border">
          <Input
            type="text"
            placeholder="Search for files (e.g., 'invoice', 'notes')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1" // Takes up remaining space
          />
          <Button onClick={handleSearch}>
            Search
          </Button>
        </div>

        {/* Results Section */}
        <div className="bg-white rounded-lg shadow-sm border min-h-[300px] p-6">
          {results.length > 0 ? (
            // Pass the results array to your FileList component
            <FileList files={results} />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <p>No files found.</p>
              <p className="text-sm">Try searching for a different term.</p>
            </div>
          )}
        </div>

      </div>
    </main>
  );
}
