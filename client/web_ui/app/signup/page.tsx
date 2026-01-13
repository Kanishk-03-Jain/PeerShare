"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import Link from "next/link";

import {
  CardTitle,
  CardDescription,
  CardHeader,
  CardContent,
  CardFooter,
  Card,
} from "@/components/ui/card";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const styles = {
    container: "w-full max-w-md",
    header: "space-y-1",
    title: "text-3xl font-bold text-black-500",
    content: "space-y-4",
    fieldGroup: "space-y-2",
    footer: "flex flex-col",
    button: "w-full",
    prompt: "mt-4 text-center text-sm",
    link: "ml-2 text-black-500",
    error: "text-sm text-red-500 font-medium",
};

export default function SignupForm() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");
    const router = useRouter();

    const handleSignUp = async (e: React.FormEvent) => {
        e.preventDefault(); // stop page reload
        setError("");
        
        if (username.length < 3) {
            setError("Username must be at least 3 characters long.");
            return;
        }
        if (password.length < 8) {
            setError("Password must be at least 8 characters long.");
            return;
        }
        try {
            await apiRequest("/api/signup", {
                method: "POST",
                body: JSON.stringify({ username, password, email }),
                credentials: "include"
            });
            router.push("/");   // redirect to dashboard

        } catch (err: any) {
            console.log(err)
            if (err?.type === "validation") {
                const passwordErr = err.errors[0].msg;
                setError(passwordErr || "Invalid Input")
            } else if (err?.type === "generic") {
                setError(err.message);
            } else {
                setError("An unknown error occurred");
            }
        }
    }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-50 px-4">
        <div className={styles.container}>
        <form onSubmit={handleSignUp}>
            <Card>
            <CardHeader className={styles.header}>
                <CardTitle className={styles.title}>Sign Up</CardTitle>
                <CardDescription>
                Enter your details to sign up to your account
                </CardDescription>
            </CardHeader>
            <CardContent className={styles.content}>
                {/* Error Message Display */}
                {error && <div className={styles.error}>{error}</div>}

                <div className={styles.fieldGroup}>
                <Label htmlFor="username">Username</Label>
                <Input
                    id="username"
                    name="username"
                    type="text"
                    placeholder="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
                </div>
                <div className={styles.fieldGroup}>
                <Label htmlFor="email">Email</Label>
                <Input
                    id="email"
                    name="email"
                    type="text"
                    placeholder="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                </div>
                <div className={styles.fieldGroup}>
                <Label htmlFor="password">Password</Label>
                <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                </div>
            </CardContent>
            <CardFooter className={styles.footer}>
                <Button className={styles.button} type="submit">
                    SignUp
                </Button>
            </CardFooter>
            </Card>
            <div className={styles.prompt}>
            Already have an account?
            <Link className={styles.link} href="login">
                Login
            </Link>
            </div>
        </form>
        </div>
    </div>
  );
}