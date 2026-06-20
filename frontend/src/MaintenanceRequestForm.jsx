import React, { useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const N8N_WEBHOOK_URL = `${API_BASE}/webhook/maintenance-request`;

export default function MaintenanceRequestForm() {
  const [form, setForm] = useState({
    tenant_name: "",
    tenant_phone: "",
    property_address: "",
    issue_description: "",
    apartment_unit: ""
  });
  const [status, setStatus] = useState("");
  const [referenceNumber, setReferenceNumber] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Sending...");
    setReferenceNumber("");
    try {
      const response = await axios.post(N8N_WEBHOOK_URL, form);
      
      // Generate a temporary reference number (will be replaced by actual from n8n response)
      const tempRef = `TM-${new Date().toISOString().split('T')[0].replace(/-/g, '')}-PENDING`;
      setReferenceNumber(response.data?.reference_number || tempRef);
      setStatus("✅ Request submitted successfully!");
      
      setForm({
        tenant_name: "",
        tenant_phone: "",
        property_address: "",
        issue_description: "",
        apartment_unit: ""
      });
    } catch (err) {
      setStatus("❌ Error sending request: " + err.message);
      setReferenceNumber("");
    }
  };

  return (
    <div style={{
      height: "100vh",
      width: "100vw",
      background: "linear-gradient(to bottom right, hsl(0, 0%, 4%) 0%, hsl(220, 15%, 10%) 50%, hsl(0, 0%, 4%) 100%)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "1rem",
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position: "fixed",
      top: 0,
      left: 0,
      overflow: "auto"
    }}>
      {/* Massive glowing orbs - matching landing page */}
      <div style={{
        position: "absolute",
        top: "-20%",
        left: "-20%",
        width: "800px",
        height: "800px",
        background: "radial-gradient(circle, rgba(0, 212, 255, 0.4) 0%, rgba(0, 212, 255, 0.1) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(80px)",
        animation: "float 8s ease-in-out infinite"
      }} />
      <div style={{
        position: "absolute",
        top: "30%",
        right: "-25%",
        width: "900px",
        height: "900px",
        background: "radial-gradient(circle, rgba(139, 92, 246, 0.35) 0%, rgba(139, 92, 246, 0.15) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(100px)",
        animation: "float 10s ease-in-out infinite reverse"
      }} />
      <div style={{
        position: "absolute",
        bottom: "-25%",
        left: "5%",
        width: "850px",
        height: "850px",
        background: "radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, rgba(99, 102, 241, 0.12) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(90px)",
        animation: "float 12s ease-in-out infinite"
      }} />
      <div style={{
        position: "absolute",
        top: "10%",
        left: "30%",
        width: "700px",
        height: "700px",
        background: "radial-gradient(circle, rgba(139, 92, 246, 0.28) 0%, rgba(139, 92, 246, 0.1) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(85px)",
        animation: "float 9s ease-in-out infinite reverse"
      }} />
      <div style={{
        position: "absolute",
        bottom: "10%",
        right: "15%",
        width: "600px",
        height: "600px",
        background: "radial-gradient(circle, rgba(0, 212, 255, 0.32) 0%, rgba(0, 212, 255, 0.1) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(75px)",
        animation: "float 11s ease-in-out infinite"
      }} />

      {/* Small floating dots */}
      <div style={{
        position: "absolute",
        top: "20%",
        left: "15%",
        width: "4px",
        height: "4px",
        background: "#00d4ff",
        borderRadius: "50%",
        opacity: "0.6",
        animation: "float 6s ease-in-out infinite"
      }} />
      <div style={{
        position: "absolute",
        top: "15%",
        right: "20%",
        width: "6px",
        height: "6px",
        background: "#6366f1",
        borderRadius: "50%",
        opacity: "0.5",
        animation: "float 7s ease-in-out infinite reverse"
      }} />
      <div style={{
        position: "absolute",
        bottom: "25%",
        left: "10%",
        width: "5px",
        height: "5px",
        background: "#8b5cf6",
        borderRadius: "50%",
        opacity: "0.6",
        animation: "float 8s ease-in-out infinite"
      }} />
      <div style={{
        position: "absolute",
        top: "45%",
        right: "12%",
        width: "4px",
        height: "4px",
        background: "#00d4ff",
        borderRadius: "50%",
        opacity: "0.7",
        animation: "float 9s ease-in-out infinite reverse"
      }} />
      <div style={{
        position: "absolute",
        bottom: "35%",
        right: "18%",
        width: "3px",
        height: "3px",
        background: "#6366f1",
        borderRadius: "50%",
        opacity: "0.5",
        animation: "float 10s ease-in-out infinite"
      }} />
      <div style={{
        position: "absolute",
        top: "70%",
        left: "25%",
        width: "5px",
        height: "5px",
        background: "#00d4ff",
        borderRadius: "50%",
        opacity: "0.6",
        animation: "float 11s ease-in-out infinite reverse"
      }} />
      <div style={{
        position: "absolute",
        top: "55%",
        left: "8%",
        width: "4px",
        height: "4px",
        background: "#8b5cf6",
        borderRadius: "50%",
        opacity: "0.5",
        animation: "float 7.5s ease-in-out infinite"
      }} />
      <div style={{
        position: "absolute",
        bottom: "20%",
        right: "30%",
        width: "6px",
        height: "6px",
        background: "#00d4ff",
        borderRadius: "50%",
        opacity: "0.7",
        animation: "float 8.5s ease-in-out infinite reverse"
      }} />
      
      {/* CSS Animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-20px) scale(1.1); }
        }
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.3); }
          50% { box-shadow: 0 0 30px rgba(0, 212, 255, 0.5); }
        }
      `}</style>
      <div style={{
        width: "100%",
        maxWidth: "480px",
        background: "rgba(26, 26, 26, 0.8)",
        backdropFilter: "blur(10px)",
        borderRadius: "16px",
        boxShadow: "0 25px 50px rgba(0,0,0,0.5)",
        padding: "2.5rem",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        position: "relative",
      }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <h1 style={{ 
            fontSize: "2rem", 
            fontWeight: "700", 
            color: "#ffffff", 
            margin: "0 0 0.5rem 0",
            letterSpacing: "-0.025em"
          }}>
            <span style={{ color: "#ffffff" }}>Smart</span>{" "}
            <span style={{ 
              background: "linear-gradient(135deg, #6366f1 0%, #00d4ff 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text"
            }}>
              Maintenance Form
            </span>
          </h1>
          <p style={{ 
            color: "rgba(255, 255, 255, 0.7)", 
            fontSize: "0.95rem", 
            margin: "0",
            fontWeight: "400",
            lineHeight: "1.6"
          }}>
            Submit your repair request and let our AI assistant handle the rest.
          </p>
        </div>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={labelStyle}>
              👤 Tenant Name
            </label>
          <input
            name="tenant_name"
              placeholder="Enter your full name"
            value={form.tenant_name}
            onChange={handleChange}
            required
            style={inputStyle}
          />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={labelStyle}>
              📱 Phone Number
        </label>
          <input
            name="tenant_phone"
              placeholder="(555) 123-4567"
            value={form.tenant_phone}
            onChange={handleChange}
            required
            style={inputStyle}
          />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={labelStyle}>
              🏢 Property Address
        </label>
          <input
            name="property_address"
              placeholder="123 Main Street, City, State"
            value={form.property_address}
            onChange={handleChange}
            required
            style={inputStyle}
          />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={labelStyle}>
              🏠 Apartment Unit
            </label>
            <input
              name="apartment_unit"
              placeholder="e.g., 2A, 301, Unit 5"
              value={form.apartment_unit}
              onChange={handleChange}
              required
              style={inputStyle}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={labelStyle}>
              🔧 Issue Description
        </label>
          <textarea
            name="issue_description"
              placeholder="Describe the maintenance issue in detail..."
            value={form.issue_description}
            onChange={handleChange}
            required
            rows={4}
              style={{ ...inputStyle, resize: "vertical", minHeight: "100px" }}
          />
          </div>
        <button
          type="submit"
          style={{
              background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #00d4ff 100%)",
              color: "#ffffff",
            border: "none",
              borderRadius: "12px",
              padding: "1rem 2rem",
              fontWeight: "600",
              fontSize: "1rem",
            cursor: "pointer",
              marginTop: "1rem",
              transition: "all 0.3s ease",
              boxShadow: "0 4px 20px rgba(0, 212, 255, 0.3)",
              textTransform: "none",
              letterSpacing: "0.025em",
              position: "relative",
              overflow: "hidden"
            }}
            onMouseOver={(e) => {
              e.target.style.transform = "translateY(-2px) scale(1.02)";
              e.target.style.boxShadow = "0 8px 30px rgba(0, 212, 255, 0.5)";
            }}
            onMouseOut={(e) => {
              e.target.style.transform = "translateY(0) scale(1)";
              e.target.style.boxShadow = "0 4px 20px rgba(0, 212, 255, 0.3)";
          }}
        >
          Submit Request
        </button>
          
          {status && (
            <div style={{ 
              textAlign: "center", 
              color: status.includes("Error") || status.includes("❌") ? "#ff6b6b" : "#00d4ff", 
              marginTop: "1rem",
              padding: "0.75rem",
              borderRadius: "8px",
              background: status.includes("Error") || status.includes("❌") ? "rgba(255, 107, 107, 0.1)" : "rgba(0, 212, 255, 0.1)",
              border: status.includes("Error") || status.includes("❌") ? "1px solid rgba(255, 107, 107, 0.3)" : "1px solid rgba(0, 212, 255, 0.3)",
              fontSize: "0.875rem",
              fontWeight: "500",
              backdropFilter: "blur(10px)"
            }}>
              {status}
              {referenceNumber && (
                <div style={{ marginTop: "0.75rem", fontSize: "0.875rem" }}>
                  <strong>Reference Number:</strong> <span style={{ 
                    fontFamily: "monospace", 
                    fontSize: "1rem",
                    padding: "0.25rem 0.5rem",
                    background: "rgba(0, 212, 255, 0.2)",
                    borderRadius: "4px",
                    display: "inline-block",
                    marginTop: "0.25rem"
                  }}>{referenceNumber}</span>
                  <div style={{ marginTop: "0.5rem", fontSize: "0.8rem", color: "#94a3b8" }}>
                    Save this number to check your request status
                  </div>
                </div>
              )}
            </div>
          )}

          <div style={{
            textAlign: "center",
            marginTop: "1.5rem",
            paddingTop: "1.5rem",
            borderTop: "1px solid rgba(255, 255, 255, 0.1)"
          }}>
            <a 
              href="/check-status"
              style={{
                color: "#00d4ff",
                textDecoration: "none",
                fontSize: "0.875rem",
                fontWeight: "500",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                transition: "all 0.3s ease"
              }}
              onMouseOver={(e) => e.target.style.opacity = "0.8"}
              onMouseOut={(e) => e.target.style.opacity = "1"}
            >
              🔍 Check Request Status
            </a>
          </div>
      </form>
      </div>
    </div>
  );
}

const labelStyle = {
  fontSize: "0.875rem", 
  fontWeight: "600", 
  color: "rgba(255, 255, 255, 0.9)",
  marginBottom: "0.25rem"
};

const inputStyle = {
  width: "100%",
  padding: "0.875rem 1rem",
  border: "1px solid rgba(0, 212, 255, 0.2)",
  borderRadius: "8px",
  fontSize: "1rem",
  fontFamily: 'inherit',
  outline: "none",
  boxSizing: "border-box",
  background: "rgba(26, 26, 26, 0.6)",
  transition: "all 0.3s ease",
  color: "#ffffff",
  fontWeight: "400",
  backdropFilter: "blur(10px)"
}; 