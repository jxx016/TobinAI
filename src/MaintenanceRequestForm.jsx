import React, { useState } from "react";
import axios from "axios";

const N8N_WEBHOOK_URL = "http://localhost:5678/webhook/maintainance-request"; // Change to your production URL as needed

export default function MaintenanceRequestForm() {
  const [form, setForm] = useState({
    tenant_name: "",
    tenant_phone: "",
    property_address: "",
    issue_description: "",
    handyman_phone: ""
  });
  const [status, setStatus] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Sending...");
    try {
      await axios.post(N8N_WEBHOOK_URL, form);
      setStatus("Request sent!");
      setForm({
        tenant_name: "",
        tenant_phone: "",
        property_address: "",
        issue_description: "",
        handyman_phone: ""
      });
    } catch (err) {
      setStatus("Error sending request: " + err.message);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#f0f4f8"
    }}>
      <div style={{
        maxWidth: 420,
        width: "100%",
        background: "#fff",
        borderRadius: 16,
        boxShadow: "0 4px 24px rgba(0,0,0,0.10)",
        padding: 32,
        fontFamily: 'Segoe UI',
      }}>
        <h2 style={{ textAlign: "center", marginBottom: 24, color: "#2b6cb0" }}>Submit Maintenance Request</h2>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <label style={{ fontWeight: 500 }}>Tenant Name
            <input
              name="tenant_name"
              placeholder="Tenant Name"
              value={form.tenant_name}
              onChange={handleChange}
              required
              style={inputStyle}
            />
          </label>
          <label style={{ fontWeight: 500 }}>Tenant Phone
            <input
              name="tenant_phone"
              placeholder="Tenant Phone"
              value={form.tenant_phone}
              onChange={handleChange}
              required
              style={inputStyle}
            />
          </label>
          <label style={{ fontWeight: 500 }}>Property Address
            <input
              name="property_address"
              placeholder="Property Address"
              value={form.property_address}
              onChange={handleChange}
              required
              style={inputStyle}
            />
          </label>
          <label style={{ fontWeight: 500 }}>Issue Description
            <textarea
              name="issue_description"
              placeholder="Describe the issue"
              value={form.issue_description}
              onChange={handleChange}
              required
              rows={4}
              style={{ ...inputStyle, resize: "vertical" }}
            />
          </label>
          <label style={{ fontWeight: 500 }}>Handyman Phone
            <input
              name="handyman_phone"
              placeholder="Handyman Phone"
              value={form.handyman_phone}
              onChange={handleChange}
              required
              style={inputStyle}
            />
          </label>
          <button
            type="submit"
            style={{
              background: "#2b6cb0",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "12px 0",
              fontWeight: 600,
              fontSize: 16,
              cursor: "pointer",
              marginTop: 8,
              transition: "background 0.2s"
            }}
          >
            Submit Request
          </button>
          {status && <div style={{ textAlign: "center", color: status.includes("Error") ? "#e53e3e" : "#2b6cb0", marginTop: 8 }}>{status}</div>}
        </form>
      </div>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  marginTop: 6,
  marginBottom: 2,
  padding: "10px 12px",
  border: "1px solid #cbd5e0",
  borderRadius: 6,
  fontSize: 15,
  fontFamily: 'inherit',
  outline: "none",
  boxSizing: "border-box",
  background: "#f7fafc"
}; 