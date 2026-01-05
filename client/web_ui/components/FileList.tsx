"use client"
import { useState } from "react";
import { File, HardDrive, Users, Download, Loader2 } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { apiRequest } from "@/lib/api"
import { Button } from "./ui/button"


interface Peer {
    ip: string;
    port: number;
}

interface FileData {
    file_hash: string;
    file_name: string;
    file_size: number;
    peers: Peer[];
}

// Helper to convert bytes to KB, MB, GB
const formatBytes = (bytes: number, decimals = 2) => {
    if (!+bytes) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export default function FileList({ files }: { files: FileData[] }) {
    // Track which file is currently being downloaded
    const [downloadingHash, setDownloadingHash] = useState<string | null>(null);

    if (!files || files.length === 0) {
        return (
            <div className="text-center text-gray-500 py-8">
                No files found.
            </div>
        );
    }
    
    const handleDownload = async (file: FileData) => {
        if (downloadingHash) return; // Prevent multiple clicks
        setDownloadingHash(file.file_hash);

        try {
            await apiRequest("/api/download", {
                method: "POST",
                body: JSON.stringify(file)
            });
            alert(`Starting downloading ${file.file_name}`);
        } catch (err) {
            console.error(err);
            alert("Download failed to start");
        } finally {
            setDownloadingHash(null);
        }
    };

    return (
    <div className="space-y-4">
      {files.map((file) => (
        <Card key={file.file_hash} className="hover:bg-gray-50 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            
            {/* Left Side: Icon & Name */}
            <div className="flex items-center space-x-4 overflow-hidden">
              <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                <File size={24} />
              </div>
              <div className="min-w-0">
                <p className="font-medium text-gray-900 truncate" title={file.file_name}>
                  {file.file_name}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="font-mono bg-gray-100 px-1 rounded truncate max-w-[120px]" title={file.file_hash}>
                        {file.file_hash.substring(0, 12)}...
                    </span>
                </div>
              </div>
            </div>

            {/* Middle: Metadata (Size & Peers) - Hidden on very small screens if needed */}
            <div className="flex items-center space-x-6 text-sm text-gray-500 flex-shrink-0">
              <div className="flex items-center space-x-1" title="File Size">
                <HardDrive size={16} />
                <span>{formatBytes(file.file_size)}</span>
              </div>
              
              <div className="flex items-center space-x-1" title="Active Peers">
                <Users size={16} />
                <span>{file.peers.length}</span>
              </div>
            </div>

            {/* Right Side: Action Button */}
            <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleDownload(file)}
                disabled={downloadingHash === file.file_hash}
                className="flex-shrink-0"
            >
                {downloadingHash === file.file_hash ? (
                    <Loader2 size={16} className="animate-spin mr-2" />
                ) : (
                    <Download size={16} className="mr-2" />
                )}
                {downloadingHash === file.file_hash ? "Starting..." : "Download"}
            </Button>

          </CardContent>
        </Card>
      ))}
    </div>
  );
}