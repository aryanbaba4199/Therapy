import { createBrowserRouter } from "react-router-dom";
import { MainLayout } from "@/layouts/main_layout";
import { HomePage } from "./home_page";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "*",
        element: <HomePage />,
      },
    ],
  },
]);
