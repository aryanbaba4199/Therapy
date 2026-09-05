import React from "react";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";

export const AppRoutes: React.FC = () => {
  return <RouterProvider router={router} />;
};
