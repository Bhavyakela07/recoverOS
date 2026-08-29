/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0B0F19",
        card: "#111827",
        cardBorder: "#1F2937",
        razorpayBlue: "#0C52E8",
        emeraldGreen: "#10B981",
        amberWarning: "#F59E0B",
        roseDanger: "#EF4444",
        mutedText: "#9CA3AF"
      }
    },
  },
  plugins: [],
};
