import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Console from "../phishing_correlation_console.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Console />
  </StrictMode>
);
