/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import "./eggs.ts";

createRoot(document.getElementById("root")!).render(<App />);
