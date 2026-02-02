import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: {
      "/workflow": "http://api:8000",
      "/status": "http://api:8000",
      "/results": "http://api:8000",
    },
  },
});
