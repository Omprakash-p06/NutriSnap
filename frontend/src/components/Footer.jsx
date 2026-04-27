export default function Footer() {
  return (
    <footer className="footer" style={styles.footer}>
      <div style={styles.section}>
        <h3 className="text-gradient" style={{ margin: '0 0 10px 0', fontSize: '1.5rem' }}>NutriSnap</h3>
        <p style={{ margin: 0, opacity: 0.7 }}>Healthy eating made simple.</p>
      </div>

      <div style={styles.section}>
        <h4 style={{ margin: '0 0 10px 0' }}>Product</h4>
        <p style={styles.p}>Features</p>
        <p style={styles.p}>Pricing</p>
      </div>

      <div style={styles.section}>
        <h4 style={{ margin: '0 0 10px 0' }}>Company</h4>
        <p style={styles.p}>About</p>
        <p style={styles.p}>Contact</p>
      </div>

      <div style={styles.section}>
        <h4 style={{ margin: '0 0 10px 0' }}>Legal</h4>
        <p style={styles.p}>Privacy Policy</p>
        <p style={styles.p}>Terms of Service</p>
      </div>
    </footer>
  );
}

const styles = {
  footer: {
    display: 'flex',
    justifyContent: 'space-around',
    padding: '40px 20px',
    borderTop: '1px solid var(--border)',
    marginTop: 'auto'
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start'
  },
  p: {
    margin: '4px 0',
    opacity: 0.7,
    cursor: 'pointer'
  }
};
