import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          light: "#FAFAFA",
          card: "#FFFFFF",
          subtle: "#F4F4F5",
        },
        ink: {
          primary: "#18181B",
          secondary: "#52525B",
          muted: "#71717A",
        },
        agri: {
          primary: "#15803D",
          hover: "#166534",
          light: "#DCFCE7",
        },
        conf: {
          high: "#15803D",
          medium: "#B45309",
          low: "#C2410C",
          abstain: "#B91C1C",
        },
      },
    },
  },
  plugins: [],
};

export default config;
