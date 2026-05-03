import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Heart, MessageCircle, Share2, Users } from "lucide-react";
import SpotlightCard from "../common/SpotlightCard";
import { useAuth } from "../../context/AuthContext";

/**
 * CommunityFeed
 * A glassmorphic social feed for sharing meal snaps.
 */
export default function CommunityFeed() {
  const [posts, setPosts] = useState([]);
  const { token } = useAuth();

  const fetchPosts = async () => {
    try {
      const res = await fetch("/api/social/posts", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await res.json();
      setPosts(data);
    } catch (err) {
      console.error("Failed to fetch posts:", err);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [token]);

  return (
    <section className="community-section" style={{ margin: "40px 0" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          marginBottom: "20px",
        }}
      >
        <Users size={24} color="var(--primary-amber)" />
        <h2 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700 }}>
          Snap Circle
        </h2>
      </div>

      <div
        className="community-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "20px",
        }}
      >
        {posts.map((post, idx) => (
          <motion.div
            key={post.id || post._id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: idx * 0.1 }}
          >
            <SpotlightCard
              className="glass-card post-card"
              style={{ padding: 0, overflow: "hidden" }}
            >
              <img
                src={
                  post.imageUrl ||
                  "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400"
                }
                alt={post.mealName}
                style={{ width: "100%", height: "200px", objectFit: "cover" }}
              />

              <div style={{ padding: "15px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    marginBottom: "10px",
                  }}
                >
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background: "var(--accent-mint)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#fff",
                      fontWeight: 800,
                      fontSize: "0.8rem",
                    }}
                  >
                    {post.userName[0]}
                  </div>
                  <div>
                    <div style={{ fontSize: "0.9rem", fontWeight: 700 }}>
                      {post.userName}
                    </div>
                    <div style={{ fontSize: "0.7rem", opacity: 0.6 }}>
                      {new Date(post.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: "1rem",
                    fontWeight: 600,
                    marginBottom: "4px",
                  }}
                >
                  {post.mealName}
                </div>
                <div
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--primary-amber)",
                    fontWeight: 700,
                    marginBottom: "15px",
                  }}
                >
                  {post.calories} kcal
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    borderTop: "1px solid rgba(255,255,255,0.1)",
                    paddingTop: "12px",
                  }}
                >
                  <div style={{ display: "flex", gap: "15px" }}>
                    <button
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--text)",
                        display: "flex",
                        alignItems: "center",
                        gap: "5px",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                      }}
                    >
                      <Heart size={18} /> {post.likes}
                    </button>
                    <button
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--text)",
                        display: "flex",
                        alignItems: "center",
                        gap: "5px",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                      }}
                    >
                      <MessageCircle size={18} />
                    </button>
                  </div>
                  <button
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "var(--text)",
                      cursor: "pointer",
                    }}
                  >
                    <Share2 size={18} />
                  </button>
                </div>
              </div>
            </SpotlightCard>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
