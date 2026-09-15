import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}", "./store/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        paper: "#f6f7f2",
        mint: "#8cc7a1",
        coral: "#e8755f",
        amber: "#e5b567",
        steel: "#5d7f99"
      }
    }
  },
  plugins: []
};

export default config;
