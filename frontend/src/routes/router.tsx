import { createBrowserRouter } from "react-router-dom";
import { MainLayout } from "@/layouts/main_layout";
import { HomePage } from "./home_page";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RegisterPage } from "../features/auth/pages/RegisterPage";
import { ProfilePage } from "../features/user/pages/ProfilePage";
import { ProtectedRoute } from "./protected_route";

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
        path: "login",
        element: <LoginPage />,
      },
      {
        path: "register",
        element: <RegisterPage />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "profile",
            element: <ProfilePage />,
          },
        ],
      },
      {
        path: "*",
        element: <HomePage />,
      },
    ],
  },
]);
