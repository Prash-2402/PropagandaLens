/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0A0F1E",
        surface: "#1E293B",
        primary: "#6366F1",
        "tech-fear": "#EF4444",
        "tech-dilemma": "#F97316",
        "tech-loaded": "#EAB308",
        "tech-bandwagon": "#3B82F6",
        "tech-hominem": "#8B5CF6",
        "tech-glittering": "#10B981",
        "tech-card": "#06B6D4",
        "tech-repetition": "#EC4899",
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
