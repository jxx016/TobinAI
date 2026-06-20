import React from "react";
import MaintenanceRequestForm from "./MaintenanceRequestForm";
import CheckStatusForm from "./CheckStatusForm";

function App() {
  // Simple routing based on path
  const path = window.location.pathname;

  if (path === "/check-status") {
    return <CheckStatusForm />;
  }

  return <MaintenanceRequestForm />;
}

export default App; 