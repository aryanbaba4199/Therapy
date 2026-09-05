import { createBrowserRouter } from "react-router-dom";
import { MainLayout } from "@/layouts/main_layout";
import { HomePage } from "./home_page";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RegisterPage } from "../features/auth/pages/RegisterPage";
import { TherapistDetailPage } from "../features/therapist/pages/TherapistDetailPage";
import { TherapistListPage } from "../features/therapist/pages/TherapistListPage";
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
        path: "therapists",
        element: <TherapistListPage />,
      },
      {
        path: "therapists/:id",
        element: <TherapistDetailPage />,
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
