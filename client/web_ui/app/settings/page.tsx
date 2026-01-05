"use client"
import { useState, useEffect } from "react"
import { apiRequest } from "@/lib/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"

export default function Settings() {
    const [config, setConfig] = useState({
        port: "",
        shared_folder: "",
        download_folder: "",
        ngrok_authtoken: "",
    });

    useEffect(() => {
        apiRequest("/api/config").then((data) => {
            setConfig({
                port: String(data.port),
                shared_folder: data.shared_folder,
                download_folder: data.download_folder,
                ngrok_authtoken: data.ngrok_configured,
            });
        })
    }, []);

    const handleSave = async () => {
        try {
            await apiRequest("/api/config", {
              method: "POST",
              body: JSON.stringify(config)
            });
            alert("Settings saved!");
        } catch(err) {
            alert("Failed to save");
        }
    }

    return (
    <div className="p-8 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      
      <div className="space-y-2">
        <Label>Port</Label>
        <Input 
            value={config.port} 
            onChange={(e) => setConfig({...config, port: e.target.value})} 
        />
      </div>
      <div className="space-y-2">
        <Label>Shared Folder Path</Label>
        <Input 
            value={config.shared_folder} 
            onChange={(e) => setConfig({...config, shared_folder: e.target.value})} 
        />
      </div>
      <div className="space-y-2">
        <Label>Download Folder Path</Label>
        <Input 
            value={config.download_folder} 
            onChange={(e) => setConfig({...config, download_folder: e.target.value})} 
        />
      </div>
      <div className="space-y-2">
        <Label>NGROK AUTHTOKEN</Label>
        <Input 
            value={config.ngrok_authtoken} 
            onChange={(e) => setConfig({...config, ngrok_authtoken: e.target.value})} 
        />
      </div>
      <Button onClick={handleSave}>Save Changes</Button>
    </div>
  );
}