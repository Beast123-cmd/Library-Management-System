import { redirect } from "next/navigation";

export default function Home() {
  redirect("/login");
}

// Trigger Vercel clean build with updated root directory settings

