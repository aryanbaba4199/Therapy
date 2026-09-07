import { type ReactElement, type ReactNode } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter, type MemoryRouterProps } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { I18nextProvider } from "react-i18next";
import { configureStore } from "@reduxjs/toolkit";

import { oppamTheme } from "@/theme/mui_theme";
import i18n from "@/i18n";
import { rootReducer } from "@/store/root_reducer";
import { baseApi } from "@/store/api/base_api";

export function createTestStore(preloadedState?: Record<string, unknown>) {
  return configureStore({
    reducer: rootReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({ serializableCheck: false }).concat(
        baseApi.middleware
      ),
    preloadedState,
  });
}

export type AppStore = ReturnType<typeof createTestStore>;

interface ExtendedRenderOptions extends Omit<RenderOptions, "queries"> {
  preloadedState?: Record<string, unknown>;
  store?: AppStore;
  routerProps?: MemoryRouterProps;
}

export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState,
    store = createTestStore(preloadedState),
    routerProps = {},
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: { children: ReactNode }): ReactElement {
    return (
      <Provider store={store}>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={oppamTheme}>
            <MemoryRouter {...routerProps}>{children}</MemoryRouter>
          </ThemeProvider>
        </I18nextProvider>
      </Provider>
    );
  }

  return {
    store,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

// eslint-disable-next-line react-refresh/only-export-components
export * from "@testing-library/react";
