"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { apiRequest } from "@/lib/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"

export default function Settings() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState({
    tracker_server_url: "",
    port: "",
    shared_folder: "",
    download_folder: "",
    ngrok_authtoken: "",
  });

  useEffect(() => {
    apiRequest("/api/config").then((data) => {
      setConfig({
        tracker_server_url: data.tracker_server_url,
        port: String(data.port),
        shared_folder: data.shared_folder,
        download_folder: data.download_folder,
        ngrok_authtoken: data.ngrok_configured,
      });
    })
  }, []);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await apiRequest("/api/config", {
        method: "POST",
        body: JSON.stringify(config)
      });
      alert("Settings saved!");
      router.push("/")

    } catch (err) {
      alert("Failed to save");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="space-y-2">
        <Label>Tracker Server URL</Label>
        <Input
          value={config.tracker_server_url}
          onChange={(e) => setConfig({ ...config, tracker_server_url: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>Port on which peer will be connected</Label>
        <Input
          value={config.port}
          onChange={(e) => setConfig({ ...config, port: e.target.value })}
        />
      </div>
      <div className="space-y-2">
        <Label>Shared Folder Path</Label>
        <Input
          value={config.shared_folder}
          onChange={(e) => setConfig({ ...config, shared_folder: e.target.value })}
        />
      </div>
      <div className="space-y-2">
        <Label>Download Folder Path</Label>
        <Input
          value={config.download_folder}
          onChange={(e) => setConfig({ ...config, download_folder: e.target.value })}
        />
      </div>
      <div className="space-y-2">
        <Label>NGROK AUTHTOKEN</Label>
        <Input
          value={config.ngrok_authtoken}
          onChange={(e) => setConfig({ ...config, ngrok_authtoken: e.target.value })}
        />
      </div>
      <Button onClick={handleSave} disabled={isLoading}>
        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isLoading ? "Saving..." : "Save Changes"}
      </Button>
    </div>
  );
}