import React from "react";
import { Provider } from "react-redux";
import { AppThemeProvider } from "@/theme/theme_provider";
import { store } from "@/store/store";
import { AppRoutes } from "@/routes/app_routes";
import "@/i18n"; // Ensure i18next initialized

export const App: React.FC = () => {
  return (
    <Provider store={store}>
      <AppThemeProvider>
        <AppRoutes />
      </AppThemeProvider>
    </Provider>
  );
};

export default App;
