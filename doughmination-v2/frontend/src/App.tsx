/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

// React Imports
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Component Imports
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ProtectedRoute from "@/components/ProtectedRoute";
import VisitorTracker from "@/components/VisitorTracker";

// Root Imports
import Index from "@/pages/Index";
import NotFound from "@/pages/NotFound";
import MemberDetails from "@/pages/MemberDetails";

// Coming Soon Route
import ComingSoon from "@/pages/ComingSoon";

// User Imports
import Login from "@/pages/authenticated/user/Login";
import UserProfile from "@/pages/authenticated/user/UserProfile";
import UserEdit from "@/pages/authenticated/user/UserEdit";
import Metrics from "@/pages/authenticated/user/Metrics";

// Admin Imports
import AdminDashboard from "@/pages/authenticated/admin/AdminDash";
import StatusManager from "@/pages/authenticated/admin/StatusManager";
import SwitchManager from "@/pages/authenticated/admin/SwitchManager";
import MentalHealthManager from "@/pages/authenticated/admin/MentalHealthManager";
import TagManager from "@/pages/authenticated/admin/TagManager";

// Owner Imports
import UserManager from "@/pages/authenticated/owner/UserManager";
import OwnerDash from "@/pages/authenticated/owner/OwnerDash"

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <VisitorTracker />
        <Routes>
          {/* Public routes */}
          <Route path="/fronting" element={<Index />} />
          <Route path="/" element={<Index />} />
          <Route path="/:member_id" element={<MemberDetails />} />
          <Route path="/user/login" element={<Login />} />

          {/* User routes - requires authentication only */}
          <Route path="/user/profile" element={
            <ProtectedRoute>
              <UserProfile />
            </ProtectedRoute>
          } />
          <Route path="/user/metrics" element={
            <ProtectedRoute>
              <Metrics />
            </ProtectedRoute>
          } />
          <Route path="/user/profile/edit" element={
            <ProtectedRoute>
              <UserEdit />
            </ProtectedRoute>
          } />

          {/* Admin routes - requires admin or owner permission */}
          <Route path="/admin/dash" element={
            <ProtectedRoute adminRequired={true}>
              <AdminDashboard />
            </ProtectedRoute>
          } />
          <Route path="/admin/status" element={
            <ProtectedRoute adminRequired={true}>
              <StatusManager />
            </ProtectedRoute>
          } />
          <Route path="/admin/mental" element={
            <ProtectedRoute adminRequired={true}>
              <MentalHealthManager />
            </ProtectedRoute>
          } />
          <Route path="/admin/switch" element={
            <ProtectedRoute adminRequired={true}>
              <SwitchManager />
            </ProtectedRoute>
          } />
          <Route path="/admin/tags" element={
            <ProtectedRoute adminRequired={true}>
              <TagManager />
            </ProtectedRoute>
          } />

          {/* Owner routes - requires owner permission */}
          <Route path="/owner/users" element={
            <ProtectedRoute ownerRequired={true}>
              <UserManager />
            </ProtectedRoute>
          } />
          <Route path="/owner/dash" element={
            <ProtectedRoute ownerRequired={true}>
              <OwnerDash />
            </ProtectedRoute>
          } />

          {/* Pet routes - requires pet or owner permission */}
          {/* Example pet route (uncomment when you create the PetDashboard component):
          <Route path="/pet/dash" element={
            <ProtectedRoute petRequired={true}>
              <PetDashboard />
            </ProtectedRoute>
          } />
          */}

          {/* Routes that exist but are not yet added*/}
          <Route path="/user/signup" element={<ComingSoon />}>
          </Route>

          {/* Catch-all route - must be last */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;