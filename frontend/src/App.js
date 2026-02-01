import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/catalog")
      .then((res) => res.json())
      .then((data) => {
        setCatalog(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching catalog:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <h3 style={{ padding: "20px" }}>Loading Zowe Capability Catalog...</h3>;
  }

  return (
    <div style={{ padding: "20px" }}>
      <h2>Zowe Capability Catalog</h2>

      <table border="1" width="100%">
        <thead>
          <tr>
            <th>Zowe Command</th>
            <th>Category</th>
            <th>Command Family</th>
            <th>Subsystem</th>
            <th>IBM Artifact</th>
            <th>Operation</th>
            <th>Access Pattern</th>
            <th>Response Format</th>
            <th>Intended Agent</th>
            <th>Execution Cost</th>
          </tr>
        </thead>

        <tbody>
          {catalog.map((item) => (
            <tr key={item.id}>
              <td>{item.zowe_command}</td>
              <td>{item.category}</td>
              <td>{item.command_family}</td>
              <td>{item.subsystem}</td>
              <td>{item.ibm_artifact}</td>
              <td>{item.operation}</td>
              <td>{item.access_pattern}</td>
              <td>{item.response_format}</td>
              <td>{item.intended_agent}</td>
              <td>{item.execution_cost}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
