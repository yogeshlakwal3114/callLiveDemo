import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./Component/Header";
import CallLive from "./Component/CallLive";
import HomePage from "./Component/Home"; 

const App = () => {
  return (
    <Router>
      <Routes>
        {/* Home Page Route */}
        <Route path="/" element={<HomePage />} />

        {/* Chat Page Route */}
        <Route
          path="/chat"
          element={
            <div>
              <Header />
              <CallLive />
            </div>
          }
        />
      </Routes>
    </Router>
  );
};

export default App;

