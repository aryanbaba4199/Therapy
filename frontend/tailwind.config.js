/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  important: "#root",
  theme: {
    extend: {
      colors: {
        oppam: {
          yellow: "#FFD336",
          yellowHover: "#FFDA58",
          dark: "#191301",
          black: "#1B1B1B",
          lightAmber: "#FFEBAD",
          cardBg: "#FAFBFD",
          green: "#00C996",
          coral: "#ED796C",
          whatsapp: "#27CE5C",
        },
      },
      fontFamily: {
        sans: ["Host Grotesk", "Plus Jakarta Sans", "system-ui", "sans-serif"],
        malayalam: ["Anek Malayalam", "system-ui", "sans-serif"],
        tamil: ["Anek Tamil", "system-ui", "sans-serif"],
      },
    },
  },
  corePlugins: {
    // Preflight can conflict with MUI baseline if not scoped
    preflight: true,
  },
  plugins: [],
}
