"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { BookMarked, Eye, EyeOff, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/axios";
import { useAuthStore } from "@/store/useAuthStore";
import { toast } from "sonner";
import type { AuthResponse, RegisterRequest } from "@/types/api";

const schema = z
  .object({
    email: z.string().email("Invalid email"),
    username: z
      .string()
      .min(3, "At least 3 characters")
      .max(100, "Max 100 characters"),
    password: z
      .string()
      .min(8, "At least 8 characters")
      .max(128, "Max 128 characters"),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type FormData = z.infer<typeof schema>;

export default function RegisterForm() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormData) {
    try {
      const body: RegisterRequest = {
        email: data.email,
        username: data.username,
        password: data.password,
      };
      const { data: res } = await apiClient.post<AuthResponse>("/auth/register", body);
      login(res.token.access_token, res.user);
      toast.success(`Welcome, ${res.user.username}! Your library awaits.`);
      router.push("/library");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Registration failed. Try a different email or username.";
      toast.error(msg);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-mahogany via-spine-navy to-ink flex items-center justify-center p-4">
      {/* Ambient particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="absolute w-0.5 h-8 bg-brass/10 rounded-full"
            style={{
              left: `${8 + i * 8}%`,
              top: `${20 + (i % 3) * 30}%`,
              transform: `rotate(${-10 + i * 5}deg)`,
              opacity: 0.3 + (i % 4) * 0.15,
            }}
          />
        ))}
      </div>

      <div className="relative w-full max-w-sm">
        <div className="bg-card/95 backdrop-blur-xl rounded-3xl border border-brass/20 shadow-2xl p-8">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-brass/15 border border-brass/30 flex items-center justify-center mb-4 shadow-lg">
              <BookMarked className="w-7 h-7 text-brass" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">Create Account</h1>
            <p className="text-muted-foreground text-sm mt-1">Start your knowledge journey</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">Email</label>
              <Input type="email" placeholder="you@example.com" {...register("email")} className={errors.email ? "border-destructive" : ""} />
              {errors.email && <p className="text-destructive text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">Username</label>
              <Input placeholder="librarian42" {...register("username")} className={errors.username ? "border-destructive" : ""} />
              {errors.username && <p className="text-destructive text-xs mt-1">{errors.username.message}</p>}
            </div>

            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">Password</label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Min. 8 characters"
                  {...register("password")}
                  className={`pr-10 ${errors.password ? "border-destructive" : ""}`}
                />
                <button type="button" onClick={() => setShowPassword((p) => !p)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-destructive text-xs mt-1">{errors.password.message}</p>}
            </div>

            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">Confirm Password</label>
              <Input type="password" placeholder="••••••••" {...register("confirmPassword")} className={errors.confirmPassword ? "border-destructive" : ""} />
              {errors.confirmPassword && <p className="text-destructive text-xs mt-1">{errors.confirmPassword.message}</p>}
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full bg-mahogany hover:bg-mahogany-light text-white font-semibold h-11 mt-2">
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Account"}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-brass hover:underline font-medium">Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
