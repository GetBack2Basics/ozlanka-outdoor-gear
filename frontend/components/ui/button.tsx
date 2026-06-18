import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "ghost";
};

export function Button({ className, variant = "default", ...props }: ButtonProps) {
  const variants = {
    default: "bg-slate-900 text-white hover:bg-slate-800",
    secondary: "bg-slate-200 text-slate-900 hover:bg-slate-300",
    ghost: "bg-transparent text-slate-900 hover:bg-slate-100",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
