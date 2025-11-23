"use client";

import { useState } from "react";

export default function Home() {
  const [formData, setFormData] = useState({
    jobRole: "",
    skills: "",
    experience: "",
    goal: ""
  });
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setRecommendations([]);

    try {
      const res = await fetch("http://127.0.0.1:8000/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_role: formData.jobRole.trim(),
          skills: formData.skills.trim(),
          experience: formData.experience ? parseInt(formData.experience) : null,
          goal: formData.goal.trim()
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setRecommendations(data.recommendations || []);
      
      if (data.recommendations.length === 0) {
        setError("No recommendations found. Try different keywords.");
      }
    } catch (err) {
      console.error("Error connecting to backend", err);
      setError("Failed to get recommendations. Please try again.");
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: 800, margin: "0 auto" }}>
      <h1 style={{ color: "#2c3e50", textAlign: "center" }}>
        SHL Assessment Recommendation Engine
      </h1>
      
      <form onSubmit={handleSubmit} style={{ marginBottom: 30 }}>
        <div style={{ marginBottom: 15 }}>
          <label style={{ display: "block", marginBottom: 5, fontWeight: "bold" }}>
            Job Role *
          </label>
          <input
            name="jobRole"
            placeholder="e.g., Software Engineer, Data Scientist"
            value={formData.jobRole}
            onChange={handleChange}
            required
            style={{
              width: "100%",
              padding: 10,
              border: "1px solid #ddd",
              borderRadius: 4
            }}
          />
        </div>

        <div style={{ marginBottom: 15 }}>
          <label style={{ display: "block", marginBottom: 5, fontWeight: "bold" }}>
            Skills (comma separated) *
          </label>
          <input
            name="skills"
            placeholder="e.g., python, machine learning, data analysis"
            value={formData.skills}
            onChange={handleChange}
            required
            style={{
              width: "100%",
              padding: 10,
              border: "1px solid #ddd",
              borderRadius: 4
            }}
          />
        </div>

        <div style={{ marginBottom: 15 }}>
          <label style={{ display: "block", marginBottom: 5, fontWeight: "bold" }}>
            Experience (years)
          </label>
          <input
            name="experience"
            type="number"
            placeholder="e.g., 3"
            min="0"
            max="50"
            value={formData.experience}
            onChange={handleChange}
            style={{
              width: "100%",
              padding: 10,
              border: "1px solid #ddd",
              borderRadius: 4
            }}
          />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", marginBottom: 5, fontWeight: "bold" }}>
            Career Goal
          </label>
          <input
            name="goal"
            placeholder="e.g., Become a senior developer, Switch to management"
            value={formData.goal}
            onChange={handleChange}
            style={{
              width: "100%",
              padding: 10,
              border: "1px solid #ddd",
              borderRadius: 4
            }}
          />
        </div>

        <button 
          type="submit" 
          disabled={loading}
          style={{
            width: "100%",
            padding: 12,
            backgroundColor: loading ? "#95a5a6" : "#3498db",
            color: "white",
            border: "none",
            borderRadius: 4,
            fontSize: 16,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Getting Recommendations..." : "Get Recommendations"}
        </button>
      </form>

      {error && (
        <div style={{
          padding: 15,
          backgroundColor: "#f8d7da",
          color: "#721c24",
          border: "1px solid #f5c6cb",
          borderRadius: 4,
          marginBottom: 20
        }}>
          {error}
        </div>
      )}

      {recommendations.length > 0 && (
        <div style={{ marginTop: 30 }}>
          <h2 style={{ color: "#2c3e50", borderBottom: "2px solid #3498db", paddingBottom: 10 }}>
            Recommended Assessments ({recommendations.length})
          </h2>
          <div style={{ display: "grid", gap: 15 }}>
            {recommendations.map((rec, i) => (
              <div
                key={i}
                style={{
                  padding: 20,
                  border: "1px solid #e1e8ed",
                  borderRadius: 8,
                  backgroundColor: "#f8f9fa"
                }}
              >
                <h3 style={{ margin: "0 0 10px 0", color: "#2c3e50" }}>
                  {rec.name}
                </h3>
                <p style={{ margin: "0 0 10px 0", color: "#666", lineHeight: 1.5 }}>
                  {rec.description}
                </p>
                <div style={{ 
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "center" 
                }}>
                  <span style={{
                    padding: "4px 8px",
                    backgroundColor: "#e8f4fd",
                    color: "#3498db",
                    borderRadius: 4,
                    fontSize: 14
                  }}>
                    {rec.domain} • {rec.level}
                  </span>
                  <span style={{
                    fontWeight: "bold",
                    color: "#27ae60"
                  }}>
                    Match: {(rec.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}