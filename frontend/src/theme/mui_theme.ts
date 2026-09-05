import { createTheme } from "@mui/material/styles";

export const oppamTheme = createTheme({
  palette: {
    primary: {
      main: "#FFD336",
      light: "#FFDA58",
      dark: "#E5BC24",
      contrastText: "#191301",
    },
    secondary: {
      main: "#191301",
      light: "#343434",
      dark: "#000000",
      contrastText: "#FFFFFF",
    },
    success: {
      main: "#00C996",
      light: "#63DEBF",
      dark: "#00A87D",
      contrastText: "#FFFFFF",
    },
    error: {
      main: "#ED796C",
      light: "#FF8577",
      dark: "#D65A4C",
      contrastText: "#FFFFFF",
    },
    background: {
      default: "#FFFFFF",
      paper: "#FAFBFD",
    },
    text: {
      primary: "#1B1B1B",
      secondary: "#5C5C5C",
    },
  },
  typography: {
    fontFamily: [
      "Host Grotesk",
      "Plus Jakarta Sans",
      "Anek Malayalam",
      "Anek Tamil",
      "sans-serif",
    ].join(","),
    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: "9999px",
          fontWeight: 700,
          paddingLeft: "24px",
          paddingRight: "24px",
        },
      },
    },
  },
});
