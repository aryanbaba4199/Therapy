import { createBrowserRouter } from "react-router-dom";
import { MainLayout } from "@/layouts/main_layout";
import { HomePage } from "./home_page";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RegisterPage } from "../features/auth/pages/RegisterPage";
import { TherapistDetailPage } from "../features/therapist/pages/TherapistDetailPage";
import { TherapistListPage } from "../features/therapist/pages/TherapistListPage";
import { AvailabilitySchedulePage } from "../features/availability";
import {
  BookingCheckoutPage,
  BookingConfirmationPage,
  BookingDetailPage,
  BookingHistoryPage,
} from "../features/booking";
import { PackageListPage, MyPackagesPage } from "../features/package";
import { ProfilePage } from "../features/user/pages/ProfilePage";
import {
  ClientSessionHistoryPage,
  TherapistDashboardPage,
  TherapistSessionDetailPage,
  TherapistSessionListPage,
} from "../features/session";
import { MyReviewsPage } from "../features/review";
import { SupportCenterPage, TicketDetailPage } from "../features/support";
import {
  AdminDashboardPage,
  AuditLogPage,
  BookingOperationsPage,
  FirstResponderDashboardPage,
  LeadManagementPage,
  PaymentOperationsPage,
  TherapistOperationsPage,
  UserManagementPage,
} from "../features/operations";
import { ProtectedRoute } from "./protected_route";
import { RoleProtectedRoute } from "./role_protected_route";

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
        path: "packages",
        element: <PackageListPage />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "profile",
            element: <ProfilePage />,
          },
          {
            path: "packages/my",
            element: <MyPackagesPage />,
          },
          {
            path: "therapist/schedule",
            element: <AvailabilitySchedulePage />,
          },
          {
            path: "bookings/checkout",
            element: <BookingCheckoutPage />,
          },
          {
            path: "bookings/confirmation",
            element: <BookingConfirmationPage />,
          },
          {
            path: "bookings",
            element: <BookingHistoryPage />,
          },
          {
            path: "bookings/:id",
            element: <BookingDetailPage />,
          },
          {
            path: "my-sessions",
            element: <ClientSessionHistoryPage />,
          },
          {
            path: "my-reviews",
            element: <MyReviewsPage />,
          },
          {
            path: "support",
            element: <SupportCenterPage />,
          },
          {
            path: "support/tickets/:ticketId",
            element: <TicketDetailPage />,
          },
          {
            element: (
              <RoleProtectedRoute
                allowedRoles={["therapist", "admin", "super_admin"]}
              />
            ),
            children: [
              {
                path: "therapist/dashboard",
                element: <TherapistDashboardPage />,
              },
              {
                path: "therapist/sessions",
                element: <TherapistSessionListPage />,
              },
              {
                path: "therapist/sessions/:sessionId",
                element: <TherapistSessionDetailPage />,
              },
            ],
          },
          {
            element: (
              <RoleProtectedRoute
                allowedRoles={[
                  "staff",
                  "first_responder",
                  "admin",
                  "super_admin",
                ]}
              />
            ),
            children: [
              {
                path: "operations/dashboard",
                element: <AdminDashboardPage />,
              },
              {
                path: "operations/first-responder",
                element: <FirstResponderDashboardPage />,
              },
              {
                path: "operations/leads",
                element: <LeadManagementPage />,
              },
              {
                path: "operations/users",
                element: <UserManagementPage />,
              },
              {
                path: "operations/therapists",
                element: <TherapistOperationsPage />,
              },
              {
                path: "operations/bookings",
                element: <BookingOperationsPage />,
              },
              {
                path: "operations/payments",
                element: <PaymentOperationsPage />,
              },
              {
                path: "operations/audit-logs",
                element: <AuditLogPage />,
              },
            ],
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
