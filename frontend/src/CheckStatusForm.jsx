import React, { useState } from "react";
import axios from "axios";

const N8N_STATUS_WEBHOOK = "http://localhost:5678/webhook/check-status";

export default function CheckStatusForm() {
  const [referenceNumber, setReferenceNumber] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await axios.get(`${N8N_STATUS_WEBHOOK}?ref=${referenceNumber}`);
      
      if (response.data.found) {
        setResult(response.data);
      } else {
        setError("Request not found. Please check your reference number.");
      }
    } catch (err) {
      setError("Error checking status. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'pending': return '#FFA500';
      case 'assigned': return '#00BFFF';
      case 'in_progress': return '#9370DB';
      case 'completed': return '#32CD32';
      default: return '#808080';
    }
  };

  const getStatusText = (status) => {
    switch (status?.toLowerCase()) {
      case 'pending': return 'Pending Review';
      case 'assigned': return 'Assigned to Vendor';
      case 'in_progress': return 'Work in Progress';
      case 'completed': return 'Completed';
      default: return status || 'Unknown';
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(to bottom right, hsl(0, 0%, 4%) 0%, hsl(220, 15%, 10%) 50%, hsl(0, 0%, 4%) 100%)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "1rem",
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position: "fixed",
      top: 0,
      left: 0,
      width: "100vw",
      overflow: "auto"
    }}>
      {/* Floating orbs background */}
      <div style={{
        position: "absolute",
        top: "-10%",
        left: "-10%",
        width: "700px",
        height: "700px",
        background: "radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, rgba(139, 92, 246, 0.1) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(100px)",
        animation: "float 10s ease-in-out infinite"
      }} />
      <div style={{
        position: "absolute",
        top: "30%",
        right: "-15%",
        width: "800px",
        height: "800px",
        background: "radial-gradient(circle, rgba(0, 212, 255, 0.3) 0%, rgba(0, 212, 255, 0.1) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(120px)",
        animation: "float 12s ease-in-out infinite reverse"
      }} />
      <div style={{
        position: "absolute",
        bottom: "-20%",
        left: "20%",
        width: "750px",
        height: "750px",
        background: "radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, rgba(99, 102, 241, 0.1) 40%, transparent 70%)",
        borderRadius: "50%",
        filter: "blur(110px)",
        animation: "float 11s ease-in-out infinite"
      }} />

      {/* Floating small dots */}
      {[...Array(20)].map((_, i) => (
        <div key={i} style={{
          position: "absolute",
          width: "4px",
          height: "4px",
          background: `rgba(0, 212, 255, ${0.3 + Math.random() * 0.4})`,
          borderRadius: "50%",
          top: `${Math.random() * 100}%`,
          left: `${Math.random() * 100}%`,
          animation: `float ${8 + Math.random() * 4}s ease-in-out infinite`,
          animationDelay: `${Math.random() * 2}s`
        }} />
      ))}

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-20px) scale(1.05); }
        }
      `}</style>

      <div style={{
        background: "rgba(15, 23, 42, 0.8)",
        backdropFilter: "blur(20px)",
        borderRadius: "24px",
        border: "1px solid rgba(100, 255, 218, 0.1)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
        padding: "2.5rem",
        maxWidth: "600px",
        width: "100%",
        zIndex: 10,
      }}>
        <div style={{ marginBottom: "2rem" }}>
          <a 
            href="/"
            style={{
              color: "#00d4ff",
              textDecoration: "none",
              fontSize: "0.875rem",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem"
            }}
          >
            ← Back to Submit Request
          </a>
        </div>

        <h1 style={{
          fontSize: "2rem",
          fontWeight: "700",
          marginBottom: "0.5rem",
          background: "linear-gradient(135deg, #00d4ff 0%, #00a3cc 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}>
          Check Request Status
        </h1>
        <p style={{ color: "#94a3b8", marginBottom: "2rem" }}>
          Enter your reference number to check the status of your maintenance request.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{
              display: "block",
              color: "#e2e8f0",
              fontWeight: "500",
              marginBottom: "0.5rem",
            }}>
              Reference Number
            </label>
            <input
              type="text"
              value={referenceNumber}
              onChange={(e) => setReferenceNumber(e.target.value.toUpperCase())}
              placeholder="TM-20231124-0001"
              required
              style={{
                width: "100%",
                padding: "0.875rem 1rem",
                backgroundColor: "rgba(30, 41, 59, 0.5)",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                borderRadius: "12px",
                color: "white",
                fontSize: "1rem",
                outline: "none",
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "1rem",
              background: "linear-gradient(135deg, #00d4ff 0%, #00a3cc 100%)",
              color: "white",
              fontWeight: "600",
              fontSize: "1.125rem",
              border: "none",
              borderRadius: "12px",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Checking..." : "Check Status"}
          </button>
        </form>

        {error && (
          <div style={{
            marginTop: "1.5rem",
            padding: "1rem",
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "12px",
            color: "#fca5a5",
          }}>
            {error}
          </div>
        )}

        {result && (
          <div style={{
            marginTop: "1.5rem",
            padding: "1.5rem",
            backgroundColor: "rgba(30, 41, 59, 0.5)",
            border: "1px solid rgba(148, 163, 184, 0.2)",
            borderRadius: "12px",
          }}>
            <h2 style={{
              fontSize: "1.25rem",
              fontWeight: "600",
              color: "#e2e8f0",
              marginBottom: "1rem",
            }}>
              Request Details
            </h2>

            <div style={{ marginBottom: "0.75rem" }}>
              <span style={{ color: "#94a3b8" }}>Reference: </span>
              <span style={{ color: "#e2e8f0", fontWeight: "600" }}>{result.reference}</span>
            </div>

            <div style={{ marginBottom: "0.75rem" }}>
              <span style={{ color: "#94a3b8" }}>Status: </span>
              <span style={{
                color: getStatusColor(result.status),
                fontWeight: "600",
                padding: "0.25rem 0.75rem",
                backgroundColor: `${getStatusColor(result.status)}20`,
                borderRadius: "6px",
                display: "inline-block"
              }}>
                {getStatusText(result.status)}
              </span>
            </div>

            {result.urgency && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span style={{ color: "#94a3b8" }}>Priority: </span>
                <span style={{ color: "#e2e8f0" }}>{result.urgency}</span>
              </div>
            )}

            {result.category && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span style={{ color: "#94a3b8" }}>Category: </span>
                <span style={{ color: "#e2e8f0", textTransform: "capitalize" }}>{result.category}</span>
              </div>
            )}

            {result.summary && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span style={{ color: "#94a3b8" }}>Summary: </span>
                <span style={{ color: "#e2e8f0" }}>{result.summary}</span>
              </div>
            )}

            {result.submitted && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span style={{ color: "#94a3b8" }}>Submitted: </span>
                <span style={{ color: "#e2e8f0" }}>
                  {new Date(result.submitted).toLocaleString()}
                </span>
              </div>
            )}

            {result.property && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span style={{ color: "#94a3b8" }}>Property: </span>
                <span style={{ color: "#e2e8f0" }}>{result.property} {result.unit}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

